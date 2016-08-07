# Copyright (c) 2013, Nathan Dunsworth - NFXPlugins
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the NFXPlugins nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NFXPLUGINS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

__all__ = [
  'SgField',
  'SgFieldSchemaInfo',
  'SgFieldSchemaInfo2'
]

# Python imports
import copy
import string
import threading
import weakref

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

# Set later in this file.
FIELD_RETURN_TYPES = {}

# Set later in this file.
FIELD_RETURN_TYPE_NAMES = {}

class SgFieldQueryProfiler(object):
  '''
  Field profiler.
  '''

  def __init__(self):
    self._fieldProfiles = {}

  def profile(self, sgField):
    if not ShotgunORM.config.ENABLE_FIELD_QUERY_PROFILING:
      return

    entity = sgField.parentEntity()

    if entity == None:
      return

    entityType = entity.type
    url = entity.connection().url().lower()

    field = sgField.name()

    if not self._fieldProfiles.has_key(url):
      data = {
        entityType: {
          field: 1
        }
      }

      self._fieldProfiles[url] = data
    elif not self._fieldProfiles[url].has_key(entityType):
      self._fieldProfiles[url][entityType] = {
        field: 1
      }
    elif not self._fieldProfiles[url][entityType].has_key(field):
      self._fieldProfiles[url][entityType][field] = 1
    else:
      self._fieldProfiles[url][entityType][field] += 1

  def reset(self):
    self._fieldProfiles = {}

class SgFieldSchemaInfo(object):
  '''
  Class that represents a Shotgun Entities field information.
  '''

  def __repr__(self):
    return '<%s.%s name:"%s", label:"%s", valueTypes:%s>' % (
      self.__module__,
      self.__class__.__name__,
      self.name(),
      self.label(),
      self.valueTypes()
    )

  def __init__(self, sgFieldAttribs):
    self._initialized = False

    self._commitable = sgFieldAttribs['commitable']
    self._defaultValue = sgFieldAttribs['default_value']
    self._displayValues = sgFieldAttribs['display_values']
    self._doc = sgFieldAttribs['doc']
    self._editable = sgFieldAttribs['editable']
    self._label = sgFieldAttribs['label']
    self._name = sgFieldAttribs['name']
    self._parent = sgFieldAttribs['parent']
    self._queryable = sgFieldAttribs['queryable']
    self._required = sgFieldAttribs['required']
    self._returnType = sgFieldAttribs['return_type']
    self._returnTypeName = sgFieldAttribs['return_type_name']
    self._summaryInfo = sgFieldAttribs['summary_info']
    self._valueTypes = sgFieldAttribs['value_types']
    self._validValues = sgFieldAttribs['valid_values']
    self._visible = sgFieldAttribs['visible']

    self._proj_visiblity = {}

  @classmethod
  def createSchemaData(
    cls,
    parent,
    name,
    returnType,
    defaultValue=None,
    doc=None,
    editable=False,
    label=None,
    required=False,
    returnTypeName=None,
    summaryInfo=None,
    displayValues=None,
    validTypes=None,
    validValues=None,
    visible=True
  ):
    '''
    Returns a dict that is formatted correctly and can be used to create a new
    SgFieldSchemaInfo object.

    SgField subclasses can use this to build the info data for the field instead
    of having to create the dict struct by hand.
    '''

    if isinstance(parent, ShotgunORM.SgEntity):
      parent = parent.schemaInfo().name()

    if label == None:
      label = string.capitalize(name)

    returnType = int(returnType)

    if returnTypeName == None:
      typeName = FIELD_RETURN_TYPE_NAMES.get(returnType)

      if typeName == None:
        raise RuntimeError('could not determine return type name, please specify it')

      returnTypeName = typeName

    if doc == None:
      doc = ''

    if displayValues == None:
      displayValues = {}

    if summaryInfo == None:
      summaryInfo = {}

    if validTypes == None:
      validTypes = []

    if validValues == None:
      validValues = []

    return {
      'commitable': True,
      'default_value': defaultValue,
      'display_values': displayValues,
      'doc': doc,
      'editable': bool(editable),
      'label': label,
      'name': name,
      'parent': parent,
      'queryable': True,
      'required': bool(required),
      'return_type': returnType,
      'return_type_name': returnTypeName,
      'summary_info': summaryInfo,
      'value_types': validTypes,
      'valid_values': validValues,
      'visible': visible
    }

  @classmethod
  def fromSg(cls, sgEntityName, sgEntityLabel, sgFieldName, sgSchema):
    '''
    Returns a new SgFieldSchemaInfo that is constructed from the arg "sgSchema".
    '''

    data = {
      'commitable': True,
      'display_values': {},
      'default_value': sgSchema['properties']['default_value']['value'],
      'doc': '',
      'editable': sgSchema['editable']['value'],
      'label': sgSchema['name']['value'],
      'name': sgFieldName,
      'parent': sgSchema['entity_type']['value'],
      'queryable': True,
      'required': sgSchema['mandatory']['value'],
      'return_type': FIELD_RETURN_TYPES.get(
        sgSchema['data_type']['value'],
        SgField.RETURN_TYPE_UNSUPPORTED
      ),
      'return_type_name': sgSchema['data_type']['value'],
      'summary_info': {},
      'value_types': [],
      'valid_values': [],
      'visible': sgSchema['visible']['value']
    }

    try:
      data['display_values'] = copy.deepcopy(
        sgSchema['properties']['display_values']['value']
      )
    except:
      pass

    try:
      data['value_types'] = copy.deepcopy(
        sgSchema['properties']['valid_types']['value']
      )
    except:
      pass

    try:
      data['valid_values'] = copy.deepcopy(
        sgSchema['properties']['valid_values']['value']
      )
    except:
      pass

    if data['return_type_name'] == 'summary':
      props = sgSchema['properties']

      expData = {
        'entity_type': props['query']['value']['entity_type'],
        'filters': props['query']['value']['filters'],
        'summary_type': props['summary_default']['value'],
        'summary_field': props['summary_field']['value'],
        'summary_value': props['summary_value']['value']
      }

      data['summary_info'] = copy.deepcopy(expData)

    return cls(data)

  @classmethod
  def fromXML(cls, sgEntityName, sgEntityLabel, sgXmlElement):
    '''
    Returns a new SgFieldSchemaInfo that is constructed from the arg "sgXmlElement".
    '''

    if sgXmlElement.tag != 'SgField':
      raise RuntimeError('invalid tag "%s"' % sgXmlElement.tag)

    data = {
      'commitable': True,
      'default_value': sgXmlElement.attrib.get('default_value').encode('utf-8'),
      'display_values': eval(sgXmlElement.attrib.get('display_values', '{}').encode('utf-8')),
      'doc': sgXmlElement.attrib.get('doc').encode('utf-8'),
      'editable': sgXmlElement.attrib.get('editable') == 'True',
      'label': sgXmlElement.attrib.get('label').encode('utf-8'),
      'name': sgXmlElement.attrib.get('name').encode('utf-8'),
      'parent': sgXmlElement.attrib.get('parent'),
      'queryable': True,
      'required': bool(sgXmlElement.attrib.get('required')),
      'return_type': int(sgXmlElement.attrib.get('return_type')),
      'return_type_name': sgXmlElement.attrib.get('return_type_name'),
      'summary_info': eval(sgXmlElement.attrib.get('summary_info', '{}').encode('utf-8')),
      'value_types': sgXmlElement.attrib.get('value_types', []),
      'valid_values': sgXmlElement.attrib.get('valid_values', []),
      'visible': bool(sgXmlElement.attrib.get('visible', True))
    }

    if data['default_value'] != '':
      v = data['default_value']

      if v == 'None':
        data['default_value'] = None
      elif v == 'True':
        data['default_value'] = True
      elif v == 'False':
        data['default_value'] = False

    if data['value_types'] != []:
      data['value_types'] = data['value_types'].encode('utf-8').split(',')

    if data['valid_values'] != []:
      data['valid_values'] = data['valid_values'].encode('utf-8').split(',')

    return cls(data)

  def defaultValue(self):
    '''
    Returns the default value of the field.
    '''

    return self._defaultValue

  def displayValues(self):
    '''
    Returns a dictionary containing the display names for a selection list
    field.
    '''

    return dict(self._displayValues)

  def doc(self):
    '''
    Returns the fields doc string.
    '''

    return self._doc

  def isCommitable(self):
    '''
    Returns True if the field is commitable to Shotgun.

    This is used by fields to determine if they are a user field or a field that
    is part of an Entity schema.
    '''

    return self._commitable

  def isQueryable(self):
    '''
    Returns True if the field is queryable from Shotgun.

    This is used by fields to determine if they are a user field or a field that
    is part of an Entity schema.
    '''

    return self._queryable

  def isEditable(self):
    '''
    Returns True if the field is editable.
    '''

    return self._editable

  def isUserField(self):
    '''
    Returns True if the field is a custom user field.
    '''

    return False

  def isRequired(self):
    '''
    Returns True if the field is required for the Entity.
    '''

    return self._required

  def isVisible(self):
    '''
    Returns True if the field is visible to users.
    '''

    return self._visible

  def name(self):
    '''
    Returns the name of the field used by Shotguns api.  This is NOT the user
    friendly name displayed in a web-browser.
    '''

    return self._name

  def label(self):
    '''
    Returns the name of the field visible to users.  This is the user friendly
    name displayed in a web-browser.
    '''

    return self._label

  def parentEntity(self):
    '''
    Returns the name of the parent Entity to which the field belongs to.
    '''

    return self._parent

  def returnType(self):
    '''
    Returns the SgField.RETURN_TYPE value of the field.
    '''

    return self._returnType

  def returnTypeName(self):
    '''
    Returns string that is the return type value from Shotgun.
    '''
    return self._returnTypeName

  def summaryInfo(self):
    '''
    For summary field infos this returns the data to build the search expression.
    '''

    return copy.deepcopy(self._summaryInfo)

  def toXML(self):
    '''
    Returns a ElementTree Element that represents the field info.

    See also:
    SgSchema.export(...)
    '''

    data = {
      'default_value': str(self.defaultValue()).decode('utf-8'),
      'doc': self.doc().decode('utf-8'),
      'editable': str(self.isEditable()),
      'label': self.label().decode('utf-8'),
      'name': self.name().decode('utf-8'),
      'parent': self.parentEntity(),
      'required': str(self.isRequired()),
      'return_type': str(self.returnType()),
      'return_type_name': self.returnTypeName(),
      'visible': str(self.visible())
    }

    displayValues = self.displayValues()
    summaryInfo = self.summaryInfo()
    validValues = self.validValues()
    valueTypes = self.valueTypes()

    if len(displayValues) > 0:
      data['display_values'] = str(self.displayValues()).decode('utf-8')

    if len(summaryInfo) > 0:
      data['summary_info'] = str(summaryInfo).decode('utf-8')

    if len(validValues) > 0:
      data['valid_values'] = ','.join(validValues).decode('utf-8')

    if len(valueTypes) > 0:
      data['value_types'] = ','.join(valueTypes)

    result = ET.Element(
      'SgField',
      **data
    )

    return result

  def validValues(self):
    '''
    Returns a list of valid values supported by the field.

    Returns an empty list when the field in Shotgun does not require certain
    values.
    '''

    return list(self._validValues)

  def valueTypes(self):
    '''
    Returns the supported value types of the SgField.

    Returns None when the field in Shotgun does not require certain value types.
    '''

    return self._valueTypes

  def visible(self):
    '''
    Returns True/False if the field is visible to users.
    '''

    return self._visible

class SgFieldSchemaInfo2(SgFieldSchemaInfo):
  '''

  '''

  @classmethod
  def createSchemaData(
    cls,
    parent,
    name,
    returnType,
    defaultValue=None,
    doc=None,
    editable=True,
    label=None,
    required=False,
    returnTypeName=None,
    summaryInfo=None,
    displayValues=None,
    validTypes=None,
    validValues=None
  ):
    result = SgFieldSchemaInfo.createSchemaData(
      parent,
      name,
      returnType,
      defaultValue,
      doc,
      editable,
      label,
      required,
      returnTypeName,
      summaryInfo,
      displayValues,
      validTypes,
      validValues
    )

    result['commitable'] = False
    result['queryable'] = False

    return result

  def isUserField(self):
    '''
    Returns True if the field is a custom user field.
    '''

    return True

  def setDoc(self, doc):
    '''
    Set the documentation string for the field.
    '''

    self._doc = str(doc)

  def setEditable(self, value):
    '''
    Set the fields editable state.
    '''

    self._editable = bool(value)

  def setLabel(self, label):
    '''
    Sets the fields label.
    '''

    self._label = str(label)

  def setName(self, name):
    '''
    Sets the fields name.
    '''

    self._name = str(name)

  def setParentEntity(self, sgEntityType):
    '''
    Sets the parent Entity type of the field.
    '''

    self._parent = sgEntityType

  def setValidValues(self, values):
    '''
    Sets the valid values the field excepts.
    '''

    self._validValues = list(values)

  def setValueTypes(self, valueTypes):
    '''
    Sets the valid value types the field excepts.
    '''

    self._valueTypes = list(values)

class SgField(object):
  '''
  A Class that represents a Shotgun Entity field.
  '''

  RETURN_TYPE_UNSUPPORTED = -1
  RETURN_TYPE_CHECKBOX = 0
  RETURN_TYPE_COLOR = 1
  RETURN_TYPE_COLOR2 = 2
  RETURN_TYPE_DATE = 3
  RETURN_TYPE_DATE_TIME = 4
  RETURN_TYPE_ENTITY = 5
  RETURN_TYPE_FLOAT = 6
  RETURN_TYPE_IMAGE = 7
  RETURN_TYPE_INT = 8
  RETURN_TYPE_LIST = 9
  RETURN_TYPE_MULTI_ENTITY = 10
  RETURN_TYPE_SERIALIZABLE = 11
  RETURN_TYPE_STATUS_LIST = 12
  RETURN_TYPE_SUMMARY = 13
  RETURN_TYPE_TAG_LIST = 14
  RETURN_TYPE_TEXT = 15
  RETURN_TYPE_TIMECODE = 16
  RETURN_TYPE_URL = 17

  # Custom return types should start at 201.
  RETURN_TYPE_RESERVED = 200

  __fieldclasses__ = {}

  __profiler__ = SgFieldQueryProfiler()

  def __repr__(self):
    return '<%s>' % ShotgunORM.mkEntityFieldString(self)

  def __enter__(self):
    # Grab the parent immediately and dont use self.hasParentEntity() because
    # field parents are weakref'd and you might lose the Entity.
    parent = self.parentEntity()

    # Lock the parent if the field has one.
    if parent != None:
      parent._SgEntity__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    # Grab the parent immediately and dont use self.hasParentEntity() because
    # field parents are weakref'd and you might lose the Entity.
    parent = self.parentEntity()

    # Lock the parent if the field has one.
    if parent != None:
      parent._SgEntity__lock.release()

    return False

  def __init__(self, name, label=None, sgFieldSchemaInfo=None, sgEntity=None):
    self.__parent = None
    self.__info = None

    self.__hasCommit = False
    self.__hasSyncUpdate = False
    self.__valid = False
    self.__isValidating = False

    self.__isCommitting = False
    self.__isUpdatingEvent = threading.Event(verbose=True)

    self.__isUpdatingEvent.set()

    self._value = None
    self._updateValue = None
    self._widget = None

    if sgFieldSchemaInfo == None:
      infoData = SgFieldSchemaInfo2.createSchemaData(
        None,
        name,
        self.returnType(),
        label=label
      )

      self.__setFieldSchemaInfo(
        SgFieldSchemaInfo2(infoData)
      )
    else:
      self.__setFieldSchemaInfo(sgFieldSchemaInfo)

    if sgEntity != None:
      self.__parent = weakref.ref(sgEntity)

    self.parentChanged()

  @classmethod
  def registeredFieldClasses(cls):
    '''
    Returns a dict containing all registered field classes.
    '''

    return dict(cls.__fieldclasses__)

  @classmethod
  def registerFieldClass(cls, sgFieldReturnType, sgFieldClass):
    '''
    Registers a field class.

    Args:
      * (int) sgFieldReturnType:
        SgField.RETURN_TYPE

      * (class) sgFieldClass:
        Class to use for the field return type.
    '''

    cls.__fieldclasses__[sgFieldReturnType] = sgFieldClass

  def __setParentEntity(self, parent):
    '''
    Internal function that sets the Entity the field belongs to
    '''

    if parent == None:
      self.__parent = None
    else:
      self.__parent = weakref.ref(parent)

      if self.isUserField():
        self.__info.setParentEntity(parent.schemaInfo().name())

    self.parentChanged()

  def __setFieldSchemaInfo(self, fieldInfo):
    '''

    '''

    self.__info = fieldInfo

  def canSync(self):
    '''
    Returns True if the field is in a state that can be updated by a sync call.

    Fields that return False for isQueryable() will always cause this to return
    False.
    '''

    parent = self.parentEntity()

    if not self.isQueryable() or parent == None or not parent.exists():
      return False

    return not (self.isValid() or self.hasSyncUpdate() or self.isSyncUpdating())

  def changed(self):
    '''
    Called whenever the fields value changes.

    This calls updateWidget() and if the field has a parent Entity it calls
    the Entities fieldChanged() with self.
    '''

    # Do not do anything if the field is validating, validate will call changed
    # on its own!
    if self.__isValidating:
      return

    self.updateWidget()

    parent = self.parentEntity()

    if parent == None:
      return

    parent.fieldChanged(self)

  def clearSyncUpdate(self):
    '''

    '''

    self._updateValue = None
    self.__hasSyncUpdate = False

  def defaultValue(self):
    '''
    Returns the default value for the field.
    '''

    return self.__info.defaultValue()

  def _deleteWidget(self):
    '''
    Subclass portion of SgField.deleteWidget().

    Note:
      This is only called by deleteWidget() if widget() is not None.
    '''

    pass

  def deleteWidget(self):
    '''
    Deletes the widget of the field.

    Returns True if the widget existed and was in fact deleted.
    '''

    with self:
      if self.widget() != None:
        self._deleteWidget()

        return True

      return False

  def doc(self):
    '''
    Returns the fields doc string.
    '''

    return self.__info.doc()

  def eventLogFilter(self):
    '''

    '''

    parent = self.parentEntity()

    if not self.isQueryable() or parent == None:
      return None

    return [
      [
        'entity',
        'is',
        parent
      ],
      [
        'attribute_name',
        'is',
        self.name()
      ]
    ]

  def eventLogs(self, sgEventType=None, sgFields=None, sgRecordLimit=0):
    '''
    Returns the event log Entities for the field.

    When the field has no parent or the parent Entity does not yet exist in
    Shotgun an empty list is returned.

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change

      * (list) sgFields:
        List of fields to populate the results with.

      * (int) sgRecordLimit:
        Limits the amount of returned events.
    '''

    filters = self.eventLogFilter()

    if filters == None:
      return []

    order = [
      {
        'field_name': 'created_at',
        'direction': 'desc'
      }
    ]

    if sgEventType != None:
      filters.append(
        [
          'event_type',
          'is',
          sgEventType
        ]
      )

    result = self.parentEntity().connection().find(
      'EventLogEntry',
      filters,
      sgFields,
      order=order,
      limit=sgRecordLimit
    )

    return result

  def _fromFieldData(self, sgData):
    '''
    Subclass portion of SgField.fromFieldData().

    Note:
      Subclasses only need to convert the incoming data to their internal
      format and return True.

      You should check if the incoming value is the same as the current value
      and in those cases do nothing and return False.

      valid() and hasCommit() are set based upon the return result of True/False.

    Args:
      * (dict) sgData:
        Dict of Shotgun formatted Entity field values.
    '''

    return False

  def fromFieldData(self, sgData):
    '''
    Sets the fields value from data returned by a Shotgun query.

    Returns True on success.

    Args:
      * (dict) sgData:
        Dict of Shotgun formatted Entity field values.
    '''

    with self:
      ShotgunORM.LoggerField.debug('%(sgField)s.fromFieldData()', {'sgField': self})
      ShotgunORM.LoggerField.debug('    * sgData: %(sgData)s', {'sgData': sgData})

      if not self.isEditable():
        raise RuntimeError('%s is not editable!' % self)

      if not ShotgunORM.config.DISABLE_FIELD_VALIDATE_ON_SET_VALUE:
        self.validate(forReal=True)

      result = self._fromFieldData(sgData, None)

      if not result:
        return False

      self.clearSyncUpdate()

      self.setValid(True)
      self.setHasCommit(True)

      self.changed()

      return True

  def hasCommit(self):
    '''
    Returns True if the fields value has changed but it has not been published
    to the Shotgun database.
    '''

    return self.__hasCommit

  def hasParentEntity(self):
    '''
    Returns True if the field has a parent Entity.

    Note:
      Because fields weakref their parent you should not use this as a test if
      its safe to call SgField.parentEntity() as it might have been gc'd
      inbetween the two calls.
    '''

    return self.parentEntity() != None

  def hasSyncUpdate(self):
    '''
    Returns True if the fields value was retrieved from Shotgun and is awaiting
    validate to set value to it.
    '''

    return self.__hasSyncUpdate

  def _invalidate(self):
    '''
    Subclass portion of SgField.invalidate().
    '''

    pass

  def invalidate(self, force=False):
    '''
    Invalidates the stored value of the field so that the next call to value()
    will force a re-evaluate its value.

    Args:
      * (bool) force:
        Forces invalidate to execute even if isValid() is False.
    '''

    with self:
      if not self.isValid() and not self.hasSyncUpdate() and not force:
        return False

      ShotgunORM.LoggerField.debug('%(sgField)s.invalidate(force=%(force)s)', {
        'sgField': self,
        'force': force
      })

      self.__isUpdatingEvent.wait()

      self.setHasCommit(False)
      self.setHasSyncUpdate(False)
      self.setValid(False)

      self._value = self.defaultValue()
      self._updateValue = None

      self._invalidate()

      return True

  def isCacheable(self):
    '''
    Returns True if the field is cacheable.

    Default returns the value of...

    hasCommit() and (isValid() or hasSyncUpdate())

    This is queried when a an Entities __del__ is called.  If True then the
    Entity will cache the fields value on the SgConnection.
    '''

    return not self.hasCommit() and (self.isValid() or self.hasSyncUpdate())

  def isCommitting(self):
    '''
    Returns True if the field is currently being commited to Shotgun.

    When this is True the field is locked and unable to change its value.
    '''

    return self.__isCommitting

  def isCommittable(self):
    '''
    Returns True if the field is allowed to make commits to Shotgun.
    '''

    return self.__info.isQueryable()

  def isCustom(self):
    '''
    Returns True if the fields API name starts with "sg_".
    '''

    return self.name().startswith('sg_')

  def isEditable(self):
    '''
    Returns True if the field is editable in Shotgun.

    When the parent Entity does not exist in Shotgun non-editable fields are
    modifyable.
    '''

    parent = self.parentEntity()

    if parent == None:
      return self.__info.isEditable()
    else:
      return self.__info.isEditable() or not parent.exists()

  def isQueryable(self):
    '''
    Returns True if the field is queryable in Shotgun.
    '''

    return self.__info.isQueryable()

  def isSyncUpdating(self):
    '''
    Returns True if the field is retrieving its value from Shotgun.

    When this is True the field is locked and unable to change its value.
    '''

    return not self.__isUpdatingEvent.isSet()

  def isUserField(self):
    '''
    Returns True if the field is a SgUserField.
    '''

    return self.__info.isUserField()

  def isValid(self):
    '''
    Returns True if the field is valid.

    This returns False when the field hasn't yet performed a query to Shotgun
    for its value or invalidate has been called.
    '''

    return self.__valid

  def isVisible(self):
    '''
    Returns True if the field is visible to users.
    '''

    return self.__info.isVisible()

  def label(self):
    '''
    Returns the user visible string of the field.
    '''

    return self.__info.label()

  def lastEventLog(self, sgEventType=None, sgFields=None):
    '''
    Returns the last event log Entity for this field.

    If no event log exists or the Entity contains no parent or the parent does
    not yet exist in Shotgun None is returned.

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".

      * (list) sgFields:
        List of fields to populate the result with.
    '''

    events = self.eventLogs(sgEventType, sgFields, sgRecordLimit=1)

    if len(events) <= 0:
      return None

    return events[0]

  def lastModified(self):
    '''
    Returns a dict containing the last modified at and modified by
    information.
    '''

    event = self.lastModifiedEvent(['created_at', 'user'])

    if event == None:
      return None
    else:
      return {
        'modified_at': event['created_at'],
        'modified_by': event['user']
      }

  def lastModifiedAt(self):
    '''
    Returns the User Entity that last modified the fields value, None if the
    field has never been modified.
    '''

    event = self.lastModifiedEvent(['created_at'])

    if event == None:
      return None
    else:
      return event['created_at']

  def lastModifiedBy(self):
    '''
    Returns a datetime object of the fields last modification date, None if the
    field has never been modified.
    '''

    event = self.lastModifiedEvent(['user'])

    if event == None:
      return None
    else:
      return event['user']

  def lastModifiedEvent(self, sgFields=None):
    '''
    Returns the last EvenLogEntry for the last modification of the
    field.  If the field has no modifications None is returned.
    '''

    parent = self.parentEntity()

    if not parent.exists():
      return None

    eventType = 'Shotgun_%(type)s_Change' % parent

    return self.lastEventLog(
      eventType,
      sgFields
    )

  def _makeWidget(self):
    '''
    Subclass portion of SgField.makeWidget().
    '''

    return False

  def makeWidget(self):
    '''
    Creates the GUI widget for the field.

    If the widget already has been created this immediately returns.
    '''

    with self:
      if self.widget() != None:
        return True

      return self._makeWidget()

  def modifiedEvents(self, sgFields=None, limit=0):
    '''

    '''

    parent = self.parentEntity()

    if not parent.exists():
      return None

    eventType = 'Shotgun_%(type)s_Change' % parent

    return self.eventLogs(
      eventType,
      sgFields,
      limit
    )

  def name(self):
    '''
    Returns the Shotgun API string used to reference the field on an Entity.
    '''

    return self.__info.name()

  def parentChanged(self):
    '''
    Called when the fields parent Entity changes.
    '''

    pass

  def parentEntity(self):
    '''
    Returns the parent SgEntity that the field is attached to.

    Fields only weakref their parent Entity so this may return None if the
    Entity has fallen out of scope.  You should always check if the returned
    result is None before doing anything.

    In the future fields may also be allowed to exist without an Entity so this
    may possibly return None.
    '''

    if self.__parent == None:
      return None

    return self.__parent()

  def prevValue(self):
    '''

    '''

    prev = self.prevValues(1)

    if len(prev) <= 0:
      return self.defaultValue()
    else:
      return prev[0]

  def prevValues(self, limit=0):
    '''

    '''

    result = []

    events = self.modifiedEvents(['meta'], limit)

    if len(events) <= 0:
      return [self.defaultValue()]

    data_type = self.returnType()
    default = self.defaultValue()

    connection = self.parentEntity().connection()

    if data_type == ShotgunORM.SgField.RETURN_TYPE_ENTITY:
      for event in events:
        value = default

        meta = event['meta']

        old_value = meta['old_value']

        if old_value != None:
          value = connection._createEntity(
            old_value['type'],
            old_value['new_value']
          )

        result.append(value)
    elif data_type == ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY:
      qEng = connection.queryEngine()
      entities = None

      if self.hasCommit():
        with qEng:
          for i in self.valueSg():
            entities.append(connection._createEntity(i['type'], i))
      else:
        entities = self.value()

      for event in events:
        value = default

        meta = event['meta']

        removed = []

        with qEng:
          for i in meta['removed']:
            removed.append(connection._createEntity(i['type'], i))

        for i in meta['added']:
          entities.remove(i['id'])

        entities.extend(removed)

        result.append(list(entities))
    else:
      for event in events:
        result.append(event['meta']['old_value'])

    return result

  def returnType(self):
    '''
    Returns the SgEntity.RETURN_TYPE.
    '''

    return self.__info.returnType()

  def returnTypeName(self):
    '''
    Returns the SgEntity.RETURN_TYPE.
    '''

    return self.__info.returnTypeName()

  def schemaInfo(self):
    '''
    Returns the SgFieldSchemaInfo object that describes the field.
    '''

    return self.__info

  def setHasCommit(self, valid):
    '''
    Sets the commit state of the field to "valid".

    Note:
      Not thread safe!

    Args:
      * (bool) valid:
        Value of state.
    '''

    if not self.isCommittable():
      return

    self.__hasCommit = bool(valid)

  def setHasSyncUpdate(self, valid):
    '''
    Sets the update state of the field to "valid".

    Note:
      Not thread safe!

    Args:
      * (bool) valid:
        Value of state.
    '''

    self.__hasSyncUpdate = bool(valid)

  def setIsCommitting(self, valid):
    '''
    Sets the commit state of the field to "valid".

    Note:
      Not thread safe!

    Args:
      * (bool) valid:
        Value of state.
    '''

    self.__isCommitting = bool(valid)

  def setSyncUpdate(self, sgData):
    '''

    '''

    self._updateValue = sgData

    self.__hasSyncUpdate = True

  def setValid(self, valid):
    '''
    Sets the valid state of the field to "valid".

    Note:
      Not thread safe!

    Args:
      * (bool) valid:
        Value of state.
    '''

    self.__valid = bool(valid)

  def _setValue(self, sgData):
    '''
    Subclass portion of SgField.setValue().

    Default function returns False.

    Note:
      Fields store their value in the property self._value.  Do not attempt to
      store the value for the field in another property on the class as SgField
      assumes this is the location of its value and other functions interact
      with it.

      Subclasses only need to convert the incoming data to their internal
      format and return True.

      You should check if the incoming value is the same as the current value
      and return False without modfiying the fields value.

      valid() and hasCommit() are set based upon the return result of True/False.

    Args:
      * (dict) sgData:
        Dict of Shotgun formatted Entity field value.
    '''

    return False

  def setValue(self, sgData):
    '''
    Set the value of the field.

    Returns True on success.

    Args:
      * (object) sgData:
        New field value.
    '''

    with self:
      ShotgunORM.LoggerField.debug('%(sgField)s.setValue(...)', {'sgField': self})
      ShotgunORM.LoggerField.debug('    * sgData: %(sgData)s', {'sgData': sgData})

      if not self.isEditable():
        raise RuntimeError('%s is not editable!' % self)

      if not ShotgunORM.config.DISABLE_FIELD_VALIDATE_ON_SET_VALUE:
        self.validate(forReal=True)

      if sgData == None:
        sgData = self.defaultValue()

      updateResult = self._setValue(sgData)

      if not updateResult:
        if not self.isValid():
          self.setValid(True)

        return False

      self.setValid(True)
      self.setHasCommit(True)

      self.changed()

      return True

  def setValueFromShotgun(self):
    '''
    Sets the fields value to its value in the Shotgun database.

    This sets isValid() to True and hasCommit() to False.  This will clear any
    previous modifications to the field.
    '''

    with self:
      ShotgunORM.LoggerField.debug('%(sgField)s.setValueFromShotgun()', {'sgField': self})

      self.invalidate()

      sgData = self.valueSg()

      result = self.fromFieldData(sgData)

      self.setValid(True)

      if result:
        self.changed()

      return result

  def setValueToDefault(self):
    '''
    Sets the fields value its default.

    This calls SgField.fromFieldData(self.defaultValue())

    Returns True on success.
    '''

    return self.setValue(self.defaultValue())

  def _toFieldData(self):
    '''
    Subclass portion of SgField.toFieldData().
    '''

    return self._value

  def toFieldData(self):
    '''
    Returns the value of the Entity field formated for Shotgun.

    Note:
      In a multi-threaded env isValid() may be True however another thread may
      change / invalidate the field during the course of this function.  If
      you absolutely want to grab a valid value lock the Entity / field down
      before calling toFieldData.
    '''

    with self:
      self.validate(forReal=True)

      return self._toFieldData()

  def updateWidget(self):
    '''
    Tells the fields widget that it should update itself.
    '''

    widget = self.widget()

    if widget == None:
      return

    widget.update()

  def _validate(self, forReal=False):
    '''
    Subclass portion of SgField.validate().

    The return value of _validate() is what isValid() will be set to.  Return
    True if the field was properly validated and its value is True otherwise
    return False.

    For sub-classes that do not plan on implementing the setting of the fields
    value, make sure to call the base classes _validate() function.
    '''

    ShotgunORM.LoggerField.debug('%(sgField)s._validate()', {
      'sgField': self
    })

    if self.hasCommit():
      return True

    if self.hasSyncUpdate():
      ShotgunORM.LoggerField.debug('    * hasSyncUpdate()')

      # isSyncUpdating() might be True but if the search raised an exception it
      # didnt flag hasSyncUpdate() so fall back to just pulling from Shotgun
      # manually.

      try:
        self._fromFieldData(self._updateValue)

        ShotgunORM.LoggerField.debug('        + Successful!')

        return True
      except Exception, e:
        ShotgunORM.LoggerField.warn(e)

        ShotgunORM.LoggerField.debug('        + Failed!')
      finally:
        self.clearSyncUpdate()

    if forReal == True:
      return self._fromFieldData(self.valueSg())

    return False

  def validate(self, forReal=False, force=False):
    '''
    Validates the field so that isValid() returns True.

    If the field has not yet pulled its value from Shotgun validate() will do
    the pull when the arg "forReal" is True.

    Note:
      When isValid() is already True then this function returns immediately.

    Args:
      * (bool) forReal:
        When False classes should not do anything expensive such as hitting
        Shotgun.  If forReal is True then Shotgun can/should be queried.

        forReal False allows fields that have a pending update from sync to
        mark themselves as being valid.

      * (bool) force:
        Forces validate to execute even if isValid() is True.
    '''

    with self:
      self.__isValidating = True

      if self.isValid() and not force:
        self.__isValidating = False

        return False

      ShotgunORM.LoggerField.debug('%(sgField)s.validate(curState=%(state)s, forReal=%(forReal)s, force=%(force)s)', {
        'sgField': self,
        'state': self.isValid(),
        'forReal': forReal,
        'force': force
      })

      self.__isUpdatingEvent.wait()

      # Don't allow __isValidating to remain True!
      try:
        self._validate(forReal=forReal)

        if forReal and not self.isValid():
          self.setValid(True)
      finally:
        self.__isValidating = False

      if self.isValid():
        self.changed()

    return True

  def _Value(self):
    '''
    Subclass portion of SgField.value().

    This allows sub-classes to return a copy of their value so modifications
    can't be done to the internal value.

    Default returns SgField._value unchanged.
    '''

    return self._value

  def value(self):
    '''
    Returns the value of the Entity field.

    If the field has not yet been pulled from Shotgun it will call validate()
    which will pull the fields value before returning.
    '''

    self.__profiler__.profile(self)

    with self:
      if self.isValid():
        return self._Value()

      self.validate(forReal=True)

      return self._Value()

  def _valueSg(self):
    '''
    Subclass portion of SgField.valueSg().

    Subclasses can override this function to define how to retrieve their value
    from Shotgun.

    Default function calls valueSg() on the parent Entity.

    For an example of a custom valueSg see the SgFieldSummary class.
    '''

    parent = self.parentEntity()

    if parent == None or not parent.exists():
      return None

    result = self.parentEntity().valuesSg([self.name()])

    if not result.has_key(self.name()):
      raise RuntimeError('field %s.%s not found in Shotgun' % (parent.label(), self.name()))

    return result[self.name()]

  def valueSg(self):
    '''
    Returns the fields value from Shotgun.
    '''

    ShotgunORM.LoggerField.debug('%(field)s.valueSg()', {'field': self})

    return self._valueSg()

  def validValues(self):
    '''
    Returns a list of valid values supported by the field.
    '''

    return self.__info.validValues()

  def valueTypes(self):
    '''
    Returns a list of valid value types supported by the field.
    '''

    return self.__info.valueTypes()

  def widget(self):
    '''
    Subclasses can implement makeWidget so this returns some type of GUI widget
    for the field.

    Default returns None.
    '''

    with self:
      return self._widget

FIELD_RETURN_TYPES = {
  'unsupported': SgField.RETURN_TYPE_UNSUPPORTED,
  'checkbox': SgField.RETURN_TYPE_CHECKBOX,
  'color': SgField.RETURN_TYPE_COLOR,
  'color2': SgField.RETURN_TYPE_COLOR2,
  'currency': SgField.RETURN_TYPE_FLOAT,
  'date': SgField.RETURN_TYPE_DATE,
  'date_time': SgField.RETURN_TYPE_DATE_TIME,
  'duration': SgField.RETURN_TYPE_INT,
  'entity': SgField.RETURN_TYPE_ENTITY,
  'entity_type': SgField.RETURN_TYPE_LIST,
  'float': SgField.RETURN_TYPE_FLOAT,
  'image': SgField.RETURN_TYPE_IMAGE,
  'list': SgField.RETURN_TYPE_LIST,
  'multi_entity': SgField.RETURN_TYPE_MULTI_ENTITY,
  'password': SgField.RETURN_TYPE_TEXT,
  'percent': SgField.RETURN_TYPE_INT,
  'number': SgField.RETURN_TYPE_INT,
  'serializable': SgField.RETURN_TYPE_SERIALIZABLE,
  'status_list': SgField.RETURN_TYPE_STATUS_LIST,
  'summary': SgField.RETURN_TYPE_SUMMARY,
  'tag_list': SgField.RETURN_TYPE_TAG_LIST,
  'text': SgField.RETURN_TYPE_TEXT,
  'timecode': SgField.RETURN_TYPE_TIMECODE,
  'url': SgField.RETURN_TYPE_URL,
  'url_template': SgField.RETURN_TYPE_TEXT,
  'uuid': SgField.RETURN_TYPE_TEXT
}

FIELD_RETURN_TYPE_NAMES = {
  SgField.RETURN_TYPE_UNSUPPORTED: 'unsupported',
  SgField.RETURN_TYPE_CHECKBOX: 'checkbox',
  SgField.RETURN_TYPE_COLOR: 'color',
  SgField.RETURN_TYPE_COLOR2: 'color2',
  SgField.RETURN_TYPE_DATE: 'date',
  SgField.RETURN_TYPE_DATE_TIME: 'date_time',
  SgField.RETURN_TYPE_ENTITY: 'entity',
  SgField.RETURN_TYPE_FLOAT: 'float',
  SgField.RETURN_TYPE_IMAGE: 'image',
  SgField.RETURN_TYPE_INT: 'number',
  SgField.RETURN_TYPE_LIST: 'list',
  SgField.RETURN_TYPE_MULTI_ENTITY: 'multi_entity',
  SgField.RETURN_TYPE_SERIALIZABLE: 'serializable',
  SgField.RETURN_TYPE_STATUS_LIST: 'status_list',
  SgField.RETURN_TYPE_SUMMARY: 'summary',
  SgField.RETURN_TYPE_TAG_LIST: 'tag_list',
  SgField.RETURN_TYPE_TEXT: 'text',
  SgField.RETURN_TYPE_TIMECODE: 'timecode',
  SgField.RETURN_TYPE_URL: 'url'
}
