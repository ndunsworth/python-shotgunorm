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
  'SgFieldInfo'
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
    entityType = entity.type
    url = entity.session().connection().url().lower()

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

class SgFieldInfo(object):
  '''
  Class that represents a Shotgun Entities field information.
  '''

  def __str__(self):
    return self.name()

  def __repr__(self):
    return '<%s.%s name:%s, label:%s, valueTypes:%s>' % (
      self.__module__,
      self.__class__.__name__,
      self.name(),
      self.label(),
      self.valueTypes()
    )

  def __init__(self, sgFieldAttribs):
    self._initialized = False

    self._defaultValue = sgFieldAttribs['default_value']
    self._doc = sgFieldAttribs['doc']
    self._editable = sgFieldAttribs['editable']
    self._label = sgFieldAttribs['label']
    self._name = sgFieldAttribs['name']
    self._parent = sgFieldAttribs['parent']
    self._required = sgFieldAttribs['required']
    self._returnType = sgFieldAttribs['return_type']
    self._returnTypeName = sgFieldAttribs['return_type_name']
    self._summaryInfo = sgFieldAttribs['summary_info']
    self._valueTypes = sgFieldAttribs['value_types']
    self._validValues = sgFieldAttribs['valid_values']

    self._constructor = SgField.__fieldclasses__.get(self._returnType, None)

  @classmethod
  def fromSg(self, sgFieldName, sgSchema):
    '''
    Returns a new SgFieldInfo that is constructed from the arg "sgSchema".
    '''

    data = {
      'default_value': sgSchema['properties']['default_value']['value'],
      'doc': '',
      'editable': sgSchema['editable']['value'],
      'label': sgSchema['name']['value'],
      'name': sgFieldName,
      'parent': sgSchema['entity_type']['value'],
      'required': sgSchema['mandatory']['value'],
      'return_type': FIELD_RETURN_TYPES.get(
        sgSchema['data_type']['value'],
        SgField.RETURN_TYPE_UNSUPPORTED)
      ,
      'return_type_name': sgSchema['data_type']['value'],
      'summary_info': None,
      'value_types': None,
      'valid_values': []
    }

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

    return self(data)

  @classmethod
  def fromXML(self, sgXmlElement):
    '''
    Returns a new SgFieldInfo that is constructed from the arg "sgXmlElement".
    '''

    if sgXmlElement.tag != 'SgField':
      raise RuntimeError('invalid tag "%s"' % sgXmlElement.tag)

    data = {
      'default_value': sgXmlElement.attrib.get('default_value'),
      'doc': sgXmlElement.attrib.get('doc'),
      'editable': sgXmlElement.attrib.get('editable') == 'True',
      'label': sgXmlElement.attrib.get('label'),
      'name': sgXmlElement.attrib.get('name'),
      'parent': sgXmlElement.attrib.get('parent'),
      'required': bool(sgXmlElement.attrib.get('required')),
      'return_type': int(sgXmlElement.attrib.get('return_type')),
      'return_type_name': sgXmlElement.attrib.get('return_type_name'),
      'summary_info': eval(sgXmlElement.attrib.get('summary_info')),
      'value_types': sgXmlElement.attrib.get('value_types'),
      'valid_values': sgXmlElement.attrib.get('valid_values'),
    }

    if data['value_types'] == '':
      data['value_types'] = []
    else:
      data['value_types'] = data['value_types'].split(',')

    if data['valid_values'] == '':
      data['valid_values'] = []
    else:
      data['valid_values'] = data['valid_values'].split(',')

    return self(data)

  def constructor(self):
    '''
    Return the fields constructor.
    '''

    return self._constructor

  def create(self, parentEntity):
    '''
    Creates a new SgField based off the info obj.
    '''

    return self.constructor()(parentEntity, self)

  def defaultValue(self):
    '''
    Returns the default value of the field.
    '''

    return self._defaultValue

  def doc(self):
    '''
    Returns the fields doc string.
    '''

    return self._doc

  def isEditable(self):
    '''
    Returns True if the field is editable.
    '''

    return self._editable

  def isRequired(self):
    '''
    Returns True if the field is required for the Entity.
    '''

    return self._required

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

    doc = self.doc()
    editable = str(self.isEditable())
    label = self.label()
    name = self.name()
    parent = self.parentEntity()
    required = str(self.isRequired())
    return_type = str(self.returnType())
    return_type_name = self.returnTypeName()
    summary_info = str(self.summaryInfo())
    value_types = self.valueTypes()
    valid_values = self.validValues()

    if value_types == None:
      value_types = ''
    else:
      value_types = string.join(value_types, ',')

    if valid_values == None:
      valid_values = ''
    else:
      valid_values = string.join(valid_values, ',')

    result = ET.Element(
      'SgField',
      doc=doc,
      editable=editable,
      label=label,
      name=name,
      parent=parent,
      required=required,
      return_type=return_type,
      return_type_name=return_type_name,
      summary_info = summary_info,
      value_types=value_types,
      valid_values=valid_values
    )

    return result

  def validValues(self):
    '''
    Returns a list of valid values supported by the field.

    Returns an empty list when the field in Shotgun does not require certain
    values.
    '''

    result = []

    for i in self._validValues:
      result.append(i)

    return result

  def valueTypes(self):
    '''
    Returns the supported value types of the SgField.

    Returns None when the field in Shotgun does require certain value types.
    '''

    return self._valueTypes

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
  RETURN_TYPE_STATUS_LIST = 11
  RETURN_TYPE_SUMMARY = 12
  RETURN_TYPE_TAG_LIST = 13
  RETURN_TYPE_TEXT = 14
  RETURN_TYPE_URL = 15

  __fieldclasses__ = {
    RETURN_TYPE_UNSUPPORTED: None
  }

  __profiler__ = SgFieldQueryProfiler()

  def __repr__(self):
    return '<%s>' % ShotgunORM.mkEntityFieldString(self)

  def __str__(self):
    return self.name()

  def __init__(self, parentEntity, fieldInfo):
    self._parent = weakref.ref(parentEntity)
    self._info = fieldInfo

    self._value = fieldInfo.defaultValue()

    self._hasCommit = False
    self._valid = False

  @classmethod
  def registerFieldClass(self, sgFieldReturnType, sgFieldClass):
    '''
    Registers a field class.

    Args:
      * (int) sgFieldReturnType:
        SgField.RETURN_TYPE

      * (class) sgFieldClass:
        Class to use for the field return type.
    '''

    self.__fieldclasses__[sgFieldReturnType] = sgFieldClass

  def _fetch(self):
    '''
    Internal function do not call!

    SgField.value() calls this when the field is not valid.  Subclasses can
    override this function to define how to retrieve their value.

    Default function calls _fetch() on the parent Entity.

    For an example of a custom fetch see the SgFieldExpression class.
    '''

    self.parentEntity()._fetch([self.name()])

  def defaultValue(self):
    '''
    Returns the default value for the field.
    '''

    return self.info().defaultValue()

  def doc(self):
    '''
    Returns the fields doc string.
    '''

    return self.info().doc()

  def eventLogs(self, sgEventType=None, sgRecordLimit=0):
    '''
    Returns the event log Entities for this field.

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".

      * (int) sgRecordLimit:
        Limits the amount of returned events.
    '''

    parent = self.parentEntity()

    if not parent.exists():
      return []

    session = parent.session()

    filters = [
      ['entity', 'is', parent],
      ['attribute_name', 'is', self.name()]
    ]

    order = [{'field_name':'created_at','direction':'desc'}]

    if sgEventType != None:
      filters.append(['event_type', 'is', sgEventType])

    result = session.find('EventLogEntry', filters, order=order, limit=sgRecordLimit)

    return result

  def _fromFieldData(self, sgData):
    '''
    Subclass portion of SgField.fromFieldData().

    Note:
    Do not call this directly!
    '''

    return False

  def fromFieldData(self, sgData):
    '''
    Sets the fields value from data returned by a Shotgun query.

    Returns True if any fields were set.

    Args:
      * (dict) sgData:
        Dict of Shotgun formatted Entity field values.
    '''

    parent = self.parentEntity()

    parent._lock()

    try:
      if not self.isEditable():
        raise RuntimeError('%s is not editable!' % ShotgunORM.mkEntityFieldString(self))

      ShotgunORM.LoggerEntityField.debug('%(sgField)s.fromFieldData()', {'sgField': self.__repr__()})
      ShotgunORM.LoggerEntityField.debug('    * sgData: %(sgData)s', {'sgData': sgData})

      return self._fromFieldData(sgData)
    except:
      raise
    finally:
      parent._release()

  def hasUpdate(self):
    '''
    Returns True if the fields value has changed but it has not been published
    to the Shotgun database.
    '''

    return self._hasCommit

  def info(self):
    '''
    Returns the SgFieldInfo object that describes the field.
    '''

    return self._info

  def invalidate(self):
    '''
    Invalidates the stored value of the field so that the next call to
    this.value() will force a Shotgun db query for the value.

    Note:
    Do not call this esp in a threaded env unless you know what you are doing!
    '''

    # You must not invalidate an ID knob!
    if self.name() == 'id':
      return

    self._value = None
    self._hasCommit = False
    self._valid = False

  def isCustom(self):
    '''
    Returns True if the fields API name starts with "sg_".
    '''

    return self.name().startswith('sg_')

  def isEditable(self):
    '''
    Returns True if the field is editable in Shotgun.
    '''

    return self.info().isEditable()

  def isValid(self):
    '''
    Returns True if the field is valid.  This returns false when the field
    hasn't yet performed a query to Shotgun for its value or invalidate has
    been called.
    '''

    return self._valid

  def label(self):
    '''
    Returns the user visible string of the field.
    '''

    return self.info().label()

  def lastEventLog(self, sgEventType=None):
    '''
    Returns the last event log Entity for this field.

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".
    '''

    parent = self.parentEntity()

    if not parent.exists():
      return None

    session = parent.session()

    filters = [
      ['entity', 'is', parent],
      ['attribute_name', 'is', self.name()]
    ]

    order = [{'field_name':'created_at','direction':'desc'}]

    if sgEventType != None:
      filters.append(['event_type', 'is', sgEventType])

    result = session.findOne('EventLogEntry', filters, order=order)

    return result

  def name(self):
    '''
    Returns the Shotgun api string used to reference the field on an Entity.
    '''

    return self.info().name()

  def parentEntity(self):
    '''
    Returns the parent SgEntity that the field is attached to.
    '''

    return self._parent()

  def returnType(self):
    '''
    Returns the SgEntity.RETURN_TYPE.
    '''

    return self.info().returnType()

  def _setValue(self, sgData):
    '''
    Subclass portion of SgField.setValue().

    Note:
    Do not call this directly!
    '''

    return False

  def setValue(self, sgData):
    '''
    Set the value of the field to the Shotgun formatted dict passed through arg
    "sgData".

    Returns True on success.

    Args:
      * (dict) sgData:
        Dict of Shotgun formatted Entity field value.
    '''

    parent = self.parentEntity()

    parent._lock()

    try:
      if not self.isEditable():
        raise RuntimeError('%s is not editable!' % ShotgunORM.mkEntityFieldString(self))

      ShotgunORM.LoggerEntityField.debug('%(entity)s.setValue(...)', {'entity': self.__repr__()})
      ShotgunORM.LoggerEntityField.debug('    * sgData: %(sgData)s', {'sgData': sgData})

      updateResult = self._setValue(sgData)

      if not updateResult:
        return False

      self._valid = True
      self._hasCommit = True

      ShotgunORM.onFieldChanged(self)

      return True
    except:
      raise
    finally:
      parent._release()

  def _toFieldData(self, sgData):
    '''
    Subclass portion of SgField.toFieldData().

    Note:
    Do not call this directly!
    '''

    return self._value

  def toFieldData(self):
    '''
    Returns the value of the Entity field formated for Shotgun.
    '''

    parent = self.parentEntity()

    parent._lock()

    try:
      if self.isValid() or self.name() == 'id':
        return self._toFieldData()

      self._fetch()

      return self._toFieldData()
    finally:
      parent._release()

  def value(self):
    '''
    Returns the value of the Entity field.

    Note:
    This syncs with Shotgun if value() has not yet been called.  Syncing will
    always occur if the parent SgEntity the field belongs to has field caching
    turned off.
    '''

    parent = self.parentEntity()

    parent._lock()

    try:
      if self.isValid() or self.name() == 'id':
        return self._value

      # Only fetch if the parent Entity exists.
      if parent.exists():
        self._fetch()

      self.__profiler__.profile(self)

      return self._value
    finally:
      parent._release()

  def validValues(self):
    '''
    Returns a list of valid values supported by the field.
    '''

    return self.info().validValues()

  def valueTypes(self):
    '''
    Returns a list of valid value types supported by the field.
    '''

    return self.info().valueTypes()

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
  'status_list': SgField.RETURN_TYPE_STATUS_LIST,
  'summary': SgField.RETURN_TYPE_SUMMARY,
  'tag_list': SgField.RETURN_TYPE_TAG_LIST,
  'text': SgField.RETURN_TYPE_TEXT,
  'url': SgField.RETURN_TYPE_URL,
  'uuid': SgField.RETURN_TYPE_TEXT
}
