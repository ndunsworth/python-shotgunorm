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
  'SgEntity',
  'SgEntityInfo'
]

# Python imports
from exceptions import AttributeError, KeyError

import copy
import threading
import webbrowser

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

class SgEntityInfo(object):
  '''
  Class for representing basic information about a Shotgun Entity.
  '''

  def __repr__(self):
    if self.isCustom():
      return '<SgEntityInfo("%s"|"%s")>' % (self.name(), self.label())
    else:
      return '<SgEntityInfo("%s")>' % self.name()

  def __init__(self, name, label, fieldInfos):
    self._isCustom = name.startswith('CustomEntity') or name.startswith('CustomNonProjectEntity')
    self._name = str(name)
    self._label = str(label)
    self._fieldInfos = fieldInfos

  @classmethod
  def fromSg(cls, sgEntityName, sgEntityLabel, sgFieldSchemas):
    '''
    From the passed Shotgun schema info a new SgEntityInfo is returned.
    '''

    fieldInfos = {}

    for fieldName, schemaData in sgFieldSchemas.items():
      if fieldName.startswith('step_'):
        continue

      fieldInfo = ShotgunORM.SgFieldInfo.fromSg(sgEntityName, sgEntityLabel, fieldName, schemaData)

      # Skip fields that have an unsupported return type!
      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        ShotgunORM.LoggerSchema.warn(
          'ignoring unsupported return type "%s", %s.%s' % (
            fieldInfo.returnTypeName(),
            sgEntityName, fieldInfo.name()
          )
        )

        continue

      fieldInfos[fieldName] = fieldInfo

    return cls(sgEntityName, sgEntityLabel, fieldInfos)

  @classmethod
  def fromXML(cls, sgXmlElement):
    '''
    From the passed XML data a new SgEntityInfo is returned.
    '''

    if sgXmlElement.tag != 'SgEntity':
      raise RuntimeError('invalid tag "%s"' % sgXmlElement.tag)

    entityFieldInfos = {}

    fields = sgXmlElement.find('fields')

    if fields == None:
      raise RuntimeError('could not find fields element')

    entityName = sgXmlElement.attrib.get('name')
    entityLabel = sgXmlElement.attrib.get('label')

    for field in fields:
      # Skip fields that have an unsupported return type!
      fieldInfo = ShotgunORM.SgFieldInfo.fromXML(entityName, entityLabel, field)

      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        ShotgunORM.LoggerEntity.warning('field %s.%s ignored because of return type unsupported' % (fieldInfo.name(), entityName))

        continue

      entityFieldInfos[field.attrib.get('name')] = fieldInfo

    return cls(entityName, entityLabel, entityFieldInfos)

  def fieldInfo(self, sgField):
    '''
    Returns the SgFieldInfo for the field.
    '''

    return self._fieldInfos.get(sgField, None)

  def fieldInfos(self, sgReturnTypes=None):
    '''
    Returns a list of ShotgunORM.SgFieldInfo objects used by the Entity.

    Args:
      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    if sgReturnTypes == None:
      return dict(self._fieldInfos)
    elif not isinstance(sgReturnTypes, (list, tuple, set)):
      sgReturnTypes = set([sgReturnTypes])
    else:
      sgReturnTypes = set(sgReturnTypes)

    result = {}

    for name, info in self._fieldInfos.items():
      if not info.returnType() in sgReturnTypes:
        continue

      result[name] = info

    return result

  def fieldNames(self, sgReturnTypes=None):
    '''
    Returns a list of field names.
    '''

    return sorted(self.fieldInfos(sgReturnTypes).keys())

  def fieldLabels(self, sgReturnTypes=None):
    '''
    Returns a list of field labels.
    '''

    infos = self.fieldInfos(sgReturnTypes)

    result = []

    for field in sorted(infos.keys()):
      result.append(
        infos[field].label()
      )

    return result

  def hasField(self, sgField):
    '''
    Returns True if the Entity contains the specified field.
    '''

    return self._fieldInfos.has_key(sgField)

  def isCustom(self):
    '''
    Returns True if the Shotgun Entity is a custom Entity.
    '''

    return self._isCustom

  def label(self):
    '''
    Returns the Shotgun user visible name of the Entity.
    '''

    return self._label

  def name(self):
    '''
    Returns the Shotgun api name of the Entity.
    '''

    return self._name

  def toXML(self):
    '''
    Returns an ElementTree Element object that is the representation of the
    Entities info.
    '''

    result = ET.Element(
      'SgEntity',
      name=self.name(),
      label=self.label()
    )

    fieldNode = ET.Element('fields')

    fieldInfos = self.fieldInfos()

    for field in sorted(fieldInfos.keys()):
      fieldNode.append(fieldInfos[field].toXML())

    result.append(fieldNode)

    return result

class SgEntity(object):
  '''
  Base class that represents a Shotgun Entity.
  '''

  # Set by the SgEntityClassFactory, do not attempt to manually set as it will
  # be overridden.
  __classinfo__ = None

  # Populated by SgEntity.registerDefaultEntityClass().
  __defaultentityclasses__ = {}

  @classmethod
  def registerDefaultEntityClass(cls, sgEntityCls, sgEntityTypes):
    '''
    Registers a default class for an Entity type.

    Args:
      * (class) sgEntityCls:
        Class to use.

      * (list) sgEntityTypes:
        List of Entity type names that will use the class.
    '''

    if not issubclass(sgEntityCls, SgEntity):
      raise TypeError('entity class must be a sub-class of SgEntity, got %s' % sgEntityCls)

    if isinstance(sgEntityTypes, str):
      sgEntityTypes = [sgEntityTypes]

    for e in sgEntityTypes:
      if not isinstance(e, str):
        raise TypeError('expected a str in entity type list, got %s' % e)

      cls.__defaultentityclasses__[e] = sgEntityCls

  def __getattribute__(self, item):
    try:
      return super(SgEntity, self).__getattribute__(item)
    except AttributeError, e:
      try:
        fieldObj = super(SgEntity, self).__getattribute__('_fields')[item]
      except KeyError:
        raise e
      except:
        raise

      return fieldObj.value()
    except:
      raise

  def __getitem__(self, item):
    field = self.field(item)

    if field == None:
      raise KeyError('invalid field key "%s"' % item)

    return field.value()

  def __setitem__(self, item, value):
    field = self.field(item)

    if field == None:
      raise KeyError('invalid field name')

    return field.setValue(value)

  def __setattr__(self, item, value):
    try:
      fieldObj = self._fields[item]
    except (AttributeError, KeyError) as e:
      return super(SgEntity, self).__setattr__(item, value)
    except:
      raise

    return fieldObj.setValue(value)

  def __eq__(self, item):
    if isinstance(item, SgEntity):
      return self.type == item.type and self['id'] == item['id'] and \
        self.connection().url().lower() == item.connection().url().lower()
    elif isinstance(item, int):
      return self.id == item
    elif isinstance(item, str):
      return self.type == item

  def __ne__(self, item):
    return not self == item

  def __gt__(self, item):
    if isinstance(item, SgEntity):
      if self.type > item.type:
        return True

      return self.id > item.id
    elif isinstance(item, str):
      return self.type > item
    elif isinstance(item, int):
      return self.id > item

    return False

  def __lt__(self, item):
    if isinstance(item, SgEntity):
      if self.type < item.type:
        return True

      return self.id < item.id
    elif isinstance(item, str):
      return self.type < item
    elif isinstance(item, int):
      return self.id < item

    return False

  def __contains__(self, item):
    return item in self._fields

  def __enter__(self):
    self._lock()

  def __exit__(self, exc_type, exc_value, traceback):
    self._unlock()

    return False

  def __del__(self):
    self.connection()._cacheEntity(self)

  def __int__(self):
    return self.id

  def __repr__(self):
    return '<%s>' % ShotgunORM.mkEntityString(self)

  def __init__(self, sgConnection):
    self.__lock = threading.RLock()
    self.__connection = sgConnection

    self._fields = {}

    self._markedForDeletion = False
    self.__isCommitting = False

    self._hasBuiltFields = False
    self._createCompleted = False

    self._widget = None

  def _fromFieldData(self, sgData):
    '''
    Sets the Entities field values from data returned by a Shotgun query.

    This is called when the Entity object is created.

    Args:
      * (dict) sgData:
        Dictionary of Shotgun formatted data.
    '''

    with self:
      sgData = dict(sgData)

      isNewEntity = not sgData.has_key('id')

      if isNewEntity:
        sgData['id'] = -id(self)
      else:
        if sgData['id'] < 0:
          isNewEntity = True

          sgData['id'] = -id(self)

      idField = self.field('id')

      self.field('id')._value = sgData['id']

      del sgData['id']

      self.field('type')._value = self.info().name()

      if sgData.has_key('type'):
        sgData['type']

      if isNewEntity:
        for field, value in sgData.items():
          fieldObj = self.field(field)

          # Skip expression summary fields.
          if fieldObj == None or fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
            continue

          #if value == None:
          #  value = fieldObj.defaultValue()

          fieldObj.fromFieldData(value)

          #fieldObj.validate()
      else:
        for field, value in sgData.items():
          fieldObj = self.field(field)

          # Skip expression summary fields.
          if fieldObj == None or fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
            continue

          #if value == None:
          #  value = fieldObj.defaultValue()

          fieldObj._updateValue = value
          fieldObj.setHasSyncUpdate(True)

          #fieldObj.validate()

  def _lock(self):
    '''
    Internal function to lock the Entities lock.
    '''

    self.__lock.acquire()

  def _unlock(self):
    '''
    Internal function to unlock the Entities lock.
    '''

    self.__lock.release()

  def _afterCommit(self, sgBatchData, sgBatchResult, sgCommitData, sgCommitError):
    '''
    Sub-class portion of SgEntity.afterCommit().

    When sgCommitError is not None perform any cleanup but do not raise the
    exception object as that will happen later by the ShotgunORM.

    This function will always be called even when the commit to Shotgun raises
    an Exception.

    ** The Entity is still locked down when this is called **

    Args:
      * (list) sgBatchData:
        List of Shotgun formatted batch commit data.

      * (list) sgBatchResult:
        The result returned from Shotgun.

      * (dict) sgCommitData:
        Dictionary used to pass user data between beforeCommit() and
        afterCommit().

      * (Exception) sgCommitError:
        The Exception object if the commit raised an error.
    '''

    pass

  def afterCommit(self, sgBatchData, sgBatchResult, sgCommitData, sgCommitError=None):
    '''
    Called in the moments immediately after the call to Shotgun has returned.

    This function will always be called even when the commit to Shotgun raises
    an Exception.

    ** The Entity is still locked down when this is called **

    Args:
      * (dict) sgBatchData:
        List of Shotgun formatted batch commit data.

      * (list) sgBatchResult:
        The result returned from Shotgun.

      * (dict) sgCommitData:
        Dictionary used to pass user data between beforeCommit() and
        afterCommit().

      * (Exception) sgCommitError:
        The Exception object if the commit raised an error.
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.afterCommit()', {'entity': self})
    ShotgunORM.LoggerEntity.debug('    * sgBatchData: %(value)s', {'value': sgBatchData})
    ShotgunORM.LoggerEntity.debug('    * sgBatchResult: %(value)s', {'value': sgBatchResult})
    ShotgunORM.LoggerEntity.debug('    * sgCommitData: %(value)s', {'value': sgCommitData})
    ShotgunORM.LoggerEntity.debug('    * sgCommitError: %(value)s', {'value': sgCommitError})

    self.__isCommitting = False

    if sgCommitError == None:
      for batch, result in map(None, sgBatchData, sgBatchResult):
        commitType = batch['request_type']

        if commitType == 'delete':
          self._markedForDeletion = False
        elif commitType == 'revive':
          pass
        elif commitType in ['create', 'update']:
          fieldNames = batch['data'].keys()

          for field in self.fields(fieldNames).values():
            field.setIsCommitting(False)

            field.setHasCommit(False)

        if commitType == 'create':
          self.field('id')._value = result['id']
    else:
      for batch, result in map(None, sgBatchData, sgBatchResult):
        if commitType == 'delete':
          pass
        elif commitType == 'revive':
          pass
        elif commitType in ['create', 'update']:
          fieldNames = batch['data'].keys()

          for field in self.fields(fieldNames).values():
            field.setIsCommitting(False)

    error = None

    try:
      self._afterCommit(sgBatchData, sgBatchResult, sgCommitData, sgCommitError)
    except Exception, e:
      error = e

    batchDataCopy = copy.deepcopy(sgBatchData)

    try:
      ShotgunORM.afterEntityCommit(self, batchDataCopy, sgBatchResult, sgCommitData, sgCommitError)
    except Exception, e:
      if error == None:
        error = e

    if error != None:
      raise error

  def _beforeCommit(self, sgBatchData, sgCommitData):
    '''
    Subclass portion of SgEntity.beforeCommit().

    ** The Entity is locked down when this is called **

    Args:
      * (dict) sgBatchData:
        Shotgun formatted batch dictionary of the Entities commit data.

      * (dict) sgCommitData:
        Dictionary used to pass data user between beforeCommit() and
        afterCommit().
    '''

    pass

  def beforeCommit(self, sgBatchData, sgCommitData):
    '''
    This function is called in the moments before the call to Shotgun.

    ** The Entity is locked down when this is called **

    Sets SgEntity.isCommitting() to True and calls SgEntity._beforeCommit.

    Args:
      * (dict) sgBatchData:
        Shotgun formatted batch dictionary of the Entities commit data.

      * (dict) sgCommitData:
        Dictionary used to pass data user between beforeCommit() and
        afterCommit().
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.beforeCommit()', {'entity': self})
    ShotgunORM.LoggerEntity.debug('    * sgBatchData: %(value)s', {'value': sgBatchData})
    ShotgunORM.LoggerEntity.debug('    * sgCommitData: %(value)s', {'value': sgCommitData})

    self.__isCommitting = True

    for batch in sgBatchData:
      commitType = batch['request_type']

      if commitType == 'delete':
        if not self.exists():
          raise RuntimeError('unable to delete Entity which does not exist in Shotgun')
      elif commitType == 'revive':
        if not self.exists():
          raise RuntimeError('unable to delete Entity which does not exist in Shotgun')
      elif commitType in ['create', 'update']:
        fieldNames = batch['data'].keys()

        for field in self.fields(fieldNames).values():
          field.setIsCommitting(True)
      else:
        raise RuntimeError('unknown commit type %s' % commitType)

    error = None

    try:
      self._beforeCommit(sgBatchData, sgCommitData)
    except Exception, e:
      error = e

    batchDataCopy = copy.deepcopy(sgBatchData)

    try:
      ShotgunORM.beforeEntityCommit(self, batchDataCopy, sgCommitData)
    except Exception, e:
      if error == None:
        error = e

    if error != None:
      raise error

  def _buildFields(self, sgFieldInfos):
    '''
    Sub-class portion of SgEntity.buildFields().

    Default function iterates over the incoming SgFieldInfos and creates the
    fields.
    '''

    fieldClasses = ShotgunORM.SgField.__fieldclasses__

    for field in sgFieldInfos.values():
      fieldName = field.name()

      newField = fieldClasses.get(field.returnType(), None)

      self._fields[fieldName] = newField(self, field)

  def buildFields(self):
    '''
    Creates all the fields for the Entity.

    After _buildFields(...) has been called buildUserFiels() is called.

    Note:
      This is called by the class factory after the Entity has been created and
      will immediately return anytime afterwards.
    '''

    # Only build the fields once!
    if self._hasBuiltFields:
      return

    # Add the type field.
    self._fields['type'] = ShotgunORM.SgFieldType(self)
    self._fields['id'] = ShotgunORM.SgFieldID(self)

    entityFieldInfos = self.info().fieldInfos()

    # Dont pass the "id" field as its manually built as a user field.  Same
    # for the type field.
    del entityFieldInfos['id']

    self._buildFields(entityFieldInfos)

    self.buildUserFields()

    for field in self._fields.keys():
      if hasattr(self.__class__, field):
        ShotgunORM.LoggerField.warn(
          'Entity type %(entity)s field name "%(name)s confilicts with class method of same name' % {
            'entity': self.type,
            'name': field
          }
        )

    self._hasBuiltFields = True

  def _buildUserFields(self):
    '''
    Sub-class portion of SgEntity.buildFields().

    Default function adds the "type" field to Entities.
    '''

    pass

  def buildUserFields(self):
    '''
    Builds the user fields for the Entity.
    '''

    # Only build the fields once!
    if self._hasBuiltFields:
      return

    self._buildUserFields()

  def clone(self, inheritFields=[], numberOfEntities=1):
    '''
    Creates a new Entity of this Entities type and returns it.  This returned
    Entity does not exist in the Shotgun database.

    Args:
      * (list) inheritFields:
        A list of field names that will have their values copied and set in
        the returned result.

      * (int) numberOfEntities:
        The number of Entities to create.  When the value is greater then 1
        a list of Entity objects will be returned.
    '''

    with self:
      sgData = {}

      if isinstance(inheritFields, str):
        inheritFields = [inheritFields]

      if len(inheritFields) >= 1:
        validFields = []

        for field in self.fields(inheritFields):
          if not field.isQueryable() or field.type == field.RETURN_TYPE_SUMMARY:
            continue

          validFields.append(field.name())

        self.sync(validFields, ignoreValid=True, ignoreWithUpdate=True)

        sgData.update(
          self.toFieldData(inheritFields)
        )

      if sgData.has_key('id'):
        del sgData['id']

      if sgData.has_key('type'):
        del sgData['type']

      numberOfEntities = max(1, numberOfEntities)

      return self.connection().create(
        self.type,
        sgData,
        sgCommit=False,
        numberOfEntities=numberOfEntities
      )

  def commit(self, sgFields=None):
    '''
    Commits any modified Entity fields that have not yet been published to the
    Shotgun database.

    Returns True if anything modifcations were published to Shotgun.

    Args:
      * (dict) sgFields:
        List of fields to commit.  When specified only those fields will be
        commited.
    '''

    with self:
      ShotgunORM.LoggerEntity.debug('%(entity)s.commit(...)', {'entity': self})
      ShotgunORM.LoggerEntity.debug('    * sgFields: %(fields)s', {'fields': sgFields})

      batchData = self.toBatchData(sgFields)

      if len(batchData) <= 0:
        return False

      connection = self.connection()

      connection._batch(
        [
          {
            'entity': self,
            'batch_data': batchData
          }
        ]
      )

      return True

  def connection(self):
    '''
    Returns the SgConnection the Entity belongs to.
    '''

    return self.__connection

  def delete(self, sgCommit=False):
    '''
    Deletes the Entity from Shotgun.

    Args:
      * (bool) sgCommit:
        Deletes the Entity and immediately commits the change.
    '''

    with self:
      if not self.exists():
        raise RuntimeError('entity does not exist, can not generate request data for type delete')

      if sgCommit:
        self.connection().delete(self)
      else:
        self._markedForDeletion = True

  def eventLogs(self, sgEventType=None, sgRecordLimit=0):
    '''
    Returns the event log Entities for this Entity

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".

      * (int) sgRecordLimit:
        Limits the amount of returned events.
    '''

    if not self.exists():
      return []

    connection = self.connection()

    filters = [
      ['entity', 'is', self.toEntityFieldData()],
    ]

    order = [{'field_name':'created_at','direction':'desc'}]

    if sgEventType != None:
      filters.append(
        [
          'event_type',
          'is',
          sgEventType
        ]
      )

    result = connection.find(
      'EventLogEntry',
      filters=filters,
      order=order,
      limit=sgRecordLimit
    )

    return result

  def exists(self):
    '''
    Returns True if the Entity has an ID and exists in the Shotgun database
    else returns False when the Entity has yet to be created with a commit.
    '''

    return self['id'] >= 0

  def field(self, sgField):
    '''
    Returns the Entity field.

    Args:
      * (str) sgField:
        Field name.
    '''

    return self._fields.get(sgField, None)

  def _fieldChanged(self, sgField):
    '''
    Subclass portion of SgEntity.fieldChanged().

    Called when a field changes values.
    '''

    pass

  def fieldChanged(self, sgField):
    '''
    Called when a field changes values.

    If SgEntity.widget() is not None then SgEntity.widget().fieldChanged()
    will be called as well.

    Args:
      * (SgField) sgField:
        Field that changed.
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.fieldChanged("%(sgField)s")', {'entity': self, 'sgField': sgField.name()})

    self._fieldChanged(sgField)

    w = self.widget()

    if w != None:
      w.fieldChanged(sgField)

    if not self.isBuildingFields() and self._createCompleted:
      ShotgunORM.onFieldChanged(sgField)

  def fieldLabels(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns a list of the field labels associated with the Entity in Shotgun.

    The order of the returned result matches by index with the result from
    SgEntity.fieldNames(), except when the arg "sgFields" is not None.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    result = []

    # Do it this way so that the index values match between this and fieldNames().
    for field in self.fieldNames(sgFields, sgReturnTypes):
      result.append(
        self.field(field).label()
      )

    return result

  def fieldNames(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns a list of the field names associated with the Entity in Shotgun.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    return sorted(
      self.fields(sgFields, sgReturnTypes).keys()
    )

  def fields(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns a dict containing all ShotgunORM.SgField objects that belong to the
    Entity.

    When the arg "sgFields" is specified then only those field objects will be
    returned.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    if sgFields == None and sgReturnTypes == None:
      return dict(self._fields)

    if isinstance(sgFields, str):
      sgFields = [sgFields]
    elif sgFields == None:
      sgFields = self._fields.keys()

    sgFields = set(sgFields)

    if sgReturnTypes == None:
      pass
    elif not isinstance(sgReturnTypes, (list, tuple, set)):
      sgReturnTypes = [sgReturnTypes]
    else:
      sgReturnTypes = set(sgReturnTypes)

    result = {}

    if sgReturnTypes != None:
      for field in sgFields:
        fieldObj = self.field(field)

        if fieldObj == None or not fieldObj.returnType() in sgReturnTypes:
          continue

        result[field] = fieldObj
    else:
      for field in sgFields:
        fieldObj = self.field(field)

        if fieldObj == None:
          continue

        result[field] = fieldObj

    return result

  def fieldSetValues(self, sgData):
    '''
    Sets the value of mulitple fields.

    Args:
      * (dict) sgData:
        Dict of new field values.
    '''

    fields = self.fields(sgData.keys())

    if len(fields) <= 0:
      return False

    # Sync the fields so that when setValue is called the fields dont validate
    # one at a time.
    if not ShotgunORM.config.DISABLE_FIELD_VALIDATE_ON_SET_VALUE:
      self.sync(
        fields.keys(),
        ignoreValid=True,
        ignoreWithUpdate=True,
        backgroundPull=False
      )

    result = False

    for field in fields.values():
      if field.setValue(sgData[field.name()]):
        result = True

    return result

  def fieldValues(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns a dict containing the value of all specified fields.

    Use this function when you want to query multiple field values at once
    and perform the action in a single call to the Shotgun database.

    Args:
      * (list) sgFields:
        List of fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    with self:
      if sgFields == None:
        sgFields = self.fieldNames()

      filteredFields = self.fields(sgFields, sgReturnTypes)

      self.sync(
        filteredFields.keys(),
        ignoreValid=True,
        ignoreWithUpdate=True,
        backgroundPull=False
      )

      result = {}

      entityFieldTypes = [
        ShotgunORM.SgField.RETURN_TYPE_ENTITY,
        ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY
      ]

      entityFields = []

      for name, field in filteredFields.items():
        if field.returnType() in entityFieldTypes:
          entityFields.append(field)

          continue

        result[name] = field.value()

      if len(entityFields) >= 1:
        qEngine = self.connection().queryEngine()

        qEngine.block()

        try:
          for field in entityFields:
            result[field.name()] = field.value()
        finally:
          qEngine.unblock()

      return result

  def hasField(self, sgField):
    '''
    Returns True if the Entity contains the field specified.

    Args:
      * (str) sgField:
        Field name.
    '''

    return self._fields.has_key(sgField)

  def hasCommit(self):
    '''
    Returns True in any of the following cases.

      1: The Entity has yet to be created in Shotgun.
      2: The Entity has been marked for deletion.
      3: One or more fields are flaged as having pending updates.
    '''

    # Bail early if the Entity does not have an ID or it is marked for deletion.
    if not self.exists() or self.isMarkedForDeletion():
      return True

    for field in self.fields().values():
      if field.hasCommit():
        return True

    return False

  def info(self):
    '''
    Returns the SgEntityInfo object that defines this Entity.
    '''

    return self.__classinfo__

  def isBuildingFields(self):
    '''
    Returns True when the Entity is building its fields.
    '''

    return not self._hasBuiltFields

  def isCommitting(self):
    '''
    Returns True if the Entity is currently commiting to Shotgun.
    '''

    return self.__isCommitting

  def isCustom(self):
    '''
    Returns True if the Entity is a custom Shotgun entity, example CustomEntity01.
    '''

    return self.info().isCustom()

  def isMarkedForDeletion(self):
    '''
    Returns True if the Entity has been marked for deletion but has not yet
    pushed the commit to Shotgun.
    '''

    return self._markedForDeletion

  def label(self):
    '''
    Returns the user visible Shotgun label of the Entity.
    '''

    return self.info().label()

  def lastEventLog(self, sgEventType=None):
    '''
    Returns the last event log Entity for this field.

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".
    '''

    if not self.exists():
      return None

    connection = self.connection()

    filters = [
      [
        'entity',
        'is',
        self.toEntityFieldData()
      ]
    ]

    order = [
      {
        'field_name': 'created_at',
        'direction':'desc'
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

    result = connection.findOne(
      'EventLogEntry',
      filters=filters,
      order=order
    )

    return result

  def _makeWidget(self):
    '''
    Subclass portion of SgEntity.makeWidget().
    '''

    return False

  def makeWidget(self):
    '''
    Creates the GUI widget for the Entity.

    If the widget already has been created this immediately returns.
    '''

    with self:
      if self.widget() != None:
        return True

      return self._makeWidget()

  def revert(self, sgFields=None, ignoreValid=False, ignoreWithUpdate=False):
    '''
    Reverts all fields to their Shotgun db value.

    Returns True if any fields were invalidated.

    Args:
      * (list) sgFields:
        List of field names to revert.  When specified only those select fields
        will be reverted. All others will be left un-touched.

      * (bool) ignoreValid:
        Ignores fields that valid() returns True.

      * (bool) ignoreWithUpdate:
        Ignores fields that have pending updates and leaves them untouched by
        the revert operation.
    '''

    with self:
      result = False

      for field in self.fields(sgFields).values():
        if not field.isValid():
          continue

        if (field.isValid() and ignoreValid) or (field.hasCommit() and ignoreWithUpdate):
          continue

        field.invalidate()

        result = True

      return result

  def revive(self):
    '''
    Revives the Entity.
    '''

    with self:
      if not self.exists():
        raise RuntimeError('entity does not exist, can not generate request data for type revive')

      self.connection().revive(self)

  def sync(self, sgFields=None, ignoreValid=False, ignoreWithUpdate=True, backgroundPull=True):
    '''
    Syncs the Entity with Shotgun and pulls down the specified field values.
    Immediately returns if the Entity doesn't exist in Shotgun.

    Returns True if any fields synced with Shotgun.

    Note:
      Non-querable fields are immediately validated during this function even if
      the arg "backgroundPull" is set to True.

    Args:
      * (list) sgFields:
        List of field names to sync.  When specified only those select fields
        will be synced.

      * (bool) ignoreValid:
        Ignores fields that are marked as valid and leaves them untouched by
        the sync operation.

      * (bool) ignoreWithUpdate:
        Ignores fields that have pending updates and leaves them untouched by
        the sync operation.

      * (bool) backgroundPull:
        Fields that SgField.isQueryable() returns True for will pull their value
        down in a background process.
    '''

    with self:
      if not self.exists():
        return False

      result = False

      pullFields = []
      nonQueryableFields = []

      for field in self.fields(sgFields).values():
        if (ignoreWithUpdate and field.hasCommit()) or (ignoreValid and field.isValid()) or (field.hasSyncUpdate() or field.isSyncUpdating()):
          continue

        field.invalidate()

        if not field.isQueryable():
          nonQueryableFields.append(field)
        else:
          pullFields.append(field.name())

        result = True

      if len(pullFields) >= 1:
        # Only pull if the Entity exists in Shotgun!
        if backgroundPull and self.exists():
          self.connection().queryEngine().addQueue(self, pullFields)
        else:
          values = self.valuesSg(pullFields)

          for field, value in values.items():
            fieldObj = self.field(field)

            fieldObj._updateValue = value
            fieldObj.setHasSyncUpdate(True)

            # Don't slow down the sync process by calling validate!
            #fieldObj.validate()

      if len(nonQueryableFields) >= 1:
        for field in nonQueryableFields:
          field.validate()

      return result

  def toBatchData(self, sgFields=None):
    '''
    Returns a list of batch commands that can be fed to a SgConnection._batch()
    call.

    The returned list may contain multiple entries in cases where
    isMarkedForDeletion() is True and fields contain pending updates.

    Returns an empty list when nothing is to be done.

    Args:
      * (list) sgFields:
        List of fields to return batch data for.
    '''

    result = []

    if self._markedForDeletion:
      result.append(
        {
          'request_type': 'delete',
          'entity_type': self.type,
          'entity_id': self['id']
        }
      )

    data = self.toFieldUpdateData(sgFields)

    if len(data) <= 0:
      return result

    if not self.exists():
      result.append(
        {
          'request_type': 'create',
          'entity_type': self.type,
          'data': data
        }
      )
    else:
      result.append(
        {
          'request_type': 'update',
          'entity_type': self.type,
          'entity_id': self['id'],
          'data': data
        }
      )

    return result

  def toEntityFieldData(self):
    '''
    Retruns a Shotgun formatted dict search pattern used for the field value
    of another Entities search pattern.
    '''

    if not self.exists():
      raise RuntimeError('can not build search pattern for an Entity that does not exist in Shotgun')

    return {
      'type': self.type,
      'id': self['id']
    }

  def toEntitySearchPattern(self):
    '''
    Returns a Shotgun formatted search pattern that can be used to find this
    Entity in a find() and findOne() call.

    If the Entity does not exist then None is returned.
    '''

    if not self.exists():
      raise RuntimeError('can not build search pattern for an Entity that does not exist in Shotgun')

    return [
      [
        'id',
        'is',
        self['id']
      ]
    ]

  def toFieldData(self, sgFields=None):
    '''
    Returns the field data of all fields as a Shotgun formatted dict.

    Args:
      * (list) sgFields:
        List of field names to sync.  When specified only those select fields
        will be returned.
    '''

    if sgFields == None:
      sgFields = self.fieldNames()
    elif isinstance(sgFields, str):
      sgFields = [sgFields]

    with self:
      result = {}

      self.sync(sgFields, ignoreValid=True, ignoreWithUpdate=True)

      for fieldName, field in self.fields(sgFields).items():
        result[fieldName] = field.toFieldData()

    return result

  def toFieldUpdateData(self, sgFields=None):
    '''
    Returns the field data of all fields which contain a pending commit as a
    Shotgun formatted dict.

    Returns an empty dict when no fields contain a pending commit.

    Note:
      Fields which return False for isCommittable() are ommited from the result.

    Args:
      * (list) sgFields:
        List of fields to process.  When specified only those select fields will
        be returned.
    '''

    result = {}

    for fieldName, field in self.fields(sgFields).items():
      if field.hasCommit() and field.isCommittable():
        result[fieldName] = field.toFieldData()

    return result

  def valuesSg(self, sgFields=None):
    '''
    Returns field values from Shotgun for the specified fields.

    Note:
      Fields which isQueryable() returns False will not be returned in the
      result!

    Args:
      * (list) sgFields:
        List of fields to fetch from Shotgun.
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.valuesSg()', {'entity': self})
    ShotgunORM.LoggerEntity.debug('    * requested: %(sgFields)s', {'sgFields': sgFields})

    if not self.exists():
      return {}

    if sgFields == None:
      sgFields = self.fieldNames()
    elif isinstance(sgFields, str):
      sgFields = [sgFields]

    pullFields = []

    for fieldName, field in self.fields(sgFields).items():
      if not field.isQueryable():
        continue

      pullFields.append(field.name())

    result = self.connection()._sg_find_one(
      self.type,
      self.toEntitySearchPattern(),
      pullFields
    )

    del result['type']

    if not 'id' in pullFields:
      del result['id']

    return result

  def webUrl(self, openInBrowser=False):
    '''
    Returns the Shotgun URL of the Entity.

    When the Entity does not yet exist in Shotgun the returned URL will be a
    link to the "entity_type" page.

    Args:
      * (bool) openInBrowser:
        When True the Entities URL will be opened in the operating systems
        default web-browser.
    '''

    iD = self['id']

    url = self.connection().url()

    if iD <= -1:
      url += '/page/project_default?entity_type=%s' % self.type

      if self.hasField('project'):
        project = self['project']

        if project == None:
          raise RuntimeError('project field is empty, unable to build url')

        projectId = project['id']

        if projectId == None:
          raise RuntimeError('project id is empty, unable to build url')

        url += '&project_id=%d' % projectId
    else:
      url += '/detail/%s/%d' % (self.type, iD)

    if openInBrowser:
      webbrowser.open(url)

    return url

  def widget(self):
    '''
    Subclasses can implement makeWidget so this returns some type of GUI widget
    for the Entity.

    Default returns None.
    '''

    with self:
      return self._widget
