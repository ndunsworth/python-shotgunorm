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
  'SgEntitySchemaInfo'
]

# Python imports
from exceptions import AttributeError, KeyError

import atexit
import copy
import threading
import weakref
import webbrowser

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

SHUTTING_DOWN = False

def sgorm_connection_atexit():
  global SHUTTING_DOWN

  SHUTTING_DOWN = True

atexit.register(sgorm_connection_atexit)

class SgEntitySchemaInfo(object):
  '''
  Class for representing basic information about a Shotgun Entity.
  '''

  def __repr__(self):
    if self.isCustom():
      return '<SgEntitySchemaInfo("%s"|"%s")>' % (self.name(), self.label())
    else:
      return '<SgEntitySchemaInfo("%s")>' % self.name()

  def __init__(self, schema, name, label, fieldInfos, fieldInfosUnsupported):
    self._schema = schema
    self._name = str(name)
    self._label = str(label)
    self._fieldInfos = fieldInfos
    self._fieldInfosUnsupported = fieldInfosUnsupported
    self._isCustom = name.startswith('CustomEntity') or name.startswith('CustomNonProjectEntity')

  @classmethod
  def fromSg(cls, sgSchema, sgEntityName, sgEntityLabel, sgFieldSchemas):
    '''
    From the passed Shotgun schema info a new SgEntitySchemaInfo is returned.
    '''

    fieldInfos = {}
    fieldInfosUnsupported = {}

    for fieldName, schemaData in sgFieldSchemas.items():
      if fieldName.startswith('step_'):
        continue

      if sgSchema.isFieldIgnored(sgEntityName, fieldName, sgSchema.url()):
        ShotgunORM.LoggerSchema.debug(
          '            * field %s is set to be ignored, ignoring',
          fieldName
        )

        continue

      fieldInfo = ShotgunORM.SgFieldSchemaInfo.fromSg(sgEntityName, sgEntityLabel, fieldName, schemaData)

      # Skip fields that have an unsupported return type!
      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        ShotgunORM.LoggerSchema.warn(
          'ignoring unsupported return type "%s", %s.%s' % (
            fieldInfo.returnTypeName(),
            sgEntityName, fieldInfo.name()
          )
        )

        fieldInfosUnsupported[fieldName] = fieldInfo
      else:
        fieldInfos[fieldName] = fieldInfo

    result = cls(sgSchema, sgEntityName, sgEntityLabel, fieldInfos, fieldInfosUnsupported)

    try:
      ShotgunORM.onEntitySchemaInfoCreate(result)
    except Exception, e:
      ShotgunORM.LoggerORM.warn(e)
    finally:
      return result

  @classmethod
  def fromXML(cls, sgSchema, sgXmlElement):
    '''
    From the passed XML data a new SgEntitySchemaInfo is returned.
    '''

    if sgXmlElement.tag != 'SgEntity':
      raise RuntimeError('invalid tag "%s"' % sgXmlElement.tag)

    entityFieldInfos = {}
    entityFieldInfosUnsupported = {}

    fields = sgXmlElement.find('fields')

    if fields == None:
      raise RuntimeError('could not find fields element')

    entityName = sgXmlElement.attrib.get('name')
    entityLabel = sgXmlElement.attrib.get('label')

    for field in fields:
      # Skip fields that have an unsupported return type!
      fieldInfo = ShotgunORM.SgFieldSchemaInfo.fromXML(entityName, entityLabel, field)

      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        ShotgunORM.LoggerEntity.warning('field %s.%s ignored because of return type unsupported' % (fieldInfo.name(), entityName))

        entityFieldInfosUnsupported[fieldInfo.name()] = fieldInfo
      else:
        entityFieldInfos[fieldInfo.name()] = fieldInfo

    result = cls(
      sgSchema,
      entityName,
      entityLabel,
      entityFieldInfos,
      entityFieldInfosUnsupported
    )

    try:
      ShotgunORM.onEntitySchemaInfoCreate(result)
    except Exception, e:
      ShotgunORM.LoggerORM.warn(e)
    finally:
      return result

  def fieldInfo(self, sgField):
    '''
    Returns the SgFieldSchemaInfo for the field.
    '''

    return self._fieldInfos.get(sgField, None)

  def fieldInfos(self, sgReturnTypes=None):
    '''
    Returns a dict of ShotgunORM.SgFieldSchemaInfo objects used by the Entity.

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

    if len(sgReturnTypes) <= 0:
      return dict(self._fieldInfos)

    result = {}

    for name, info in self._fieldInfos.items():
      if not info.returnType() in sgReturnTypes:
        continue

      result[name] = info

    return result

  def fieldInfosUnsupported(self):
    '''
    Returns a dict of all unsupported ShotgunORM.SgFieldSchemaInfo objects.
    '''

    return dict(self._fieldInfosUnsupported)

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

  def schema(self):
    '''
    Returns the SgSchema the info was built from.
    '''

    return self._schema

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
  def defaultEntityClass(cls, sgEntityType):
    '''
    Returns the class registered with registerDefaultEntityClass for
    the specified Entity type
    '''

    return cls.__defaultentityclasses__.get(
      sgEntityType,
      cls.__defaultentityclasses__['Entity']
    )

  @classmethod
  def defaultEntityClasses(cls):
    '''
    Returns a dict of all the Entity classes registered with
    registerDefaultEntityClass(...).
    '''

    return dict(cls.__defaultentityclasses__)

  @classmethod
  def find(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().find(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def findAsync(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().findAsync(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def findIterator(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().findIterator(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def findOne(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().findOne(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def findOneAsync(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().findOneAsync(self.__sg_entity_name__, *args, **kwargs)

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

  @classmethod
  def search(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().search(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def searchAsync(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().searchAsync(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def searchIterator(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().searchIterator(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def searchOne(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().searchOne(self.__sg_entity_name__, *args, **kwargs)

  @classmethod
  def searchOneAsync(self, *args, **kwargs):
    '''

    '''

    return self.__sg_connection__().searchOneAsync(self.__sg_entity_name__, *args, **kwargs)

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
    global SHUTTING_DOWN

    if SHUTTING_DOWN == False:
      self.connection().cacheEntity(self)

  def __dir__(self):
    if ShotgunORM.config.ENTITY_DIR_INCLUDE_FIELDS:
      return sorted(
        dir(type(self)) + self.__dict__.keys() + self.fieldNames()
      )
    else:
      return sorted(
        dir(type(self)) + self.__dict__.keys()
      )

  def __int__(self):
    return self.id

  def __repr__(self):
    return '<%s>' % ShotgunORM.mkEntityString(self)

  def __init__(self):
    self.__lock = threading.RLock()

    self.__isCommitting = False
    self.__hasBuiltFields = False
    self.__caching = -1

    self._fields = {}
    self._markedForDeletion = False
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

      self.field('type')._value = self.schemaInfo().name()

      if sgData.has_key('type'):
        sgData['type']

      for field, value in sgData.items():
        fieldObj = self.field(field)

        if fieldObj == None:
          ShotgunORM.LoggerEntity.debug('%s no field named "%s"' % (self, field))

          continue

        # Skip expression summary fields.
        if fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
          continue

        fieldObj._fromFieldData(value)

        fieldObj.setValid(True)

        if isNewEntity:
          fieldObj.setHasCommit(True)

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

  def addField(self, sgField):
    '''
    Adds the passed field to the Entity.
    '''

    with self:
      if not sgField.isUserField():
        raise RuntimeError('unable to add a field from another Entity')

      fieldName = sgField.name()

      if self.hasField(fieldName):
        raise RuntimeError('Entity already has a field named "%s"' % fieldName)

      sgField._SgField__setParentEntity(self)

      self._fields[fieldName] = sgField

  def _afterCommit(self, sgBatchData, sgBatchResult, sgCommitData, dryRun, sgCommitError):
    '''
    Subclass portion of SgEntity.afterCommit().

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

  def afterCommit(self, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError=None):
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

      * (bool) sgDryRun:
        When True the commit is not updating Shotgun with any modifications,
        it is only in a test phase.

      * (Exception) sgCommitError:
        The Exception object if the commit raised an error.
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.afterCommit()', {'entity': self})
    ShotgunORM.LoggerEntity.debug('    * sgBatchData: %(value)s', {'value': sgBatchData})
    ShotgunORM.LoggerEntity.debug('    * sgBatchResult: %(value)s', {'value': sgBatchResult})
    ShotgunORM.LoggerEntity.debug('    * sgCommitData: %(value)s', {'value': sgCommitData})
    ShotgunORM.LoggerEntity.debug('    * sgDryRun: %(value)s', {'value': sgDryRun})
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

            if not sgDryRun:
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
      self._afterCommit(sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError)
    except Exception, e:
      error = e

    batchDataCopy = copy.deepcopy(sgBatchData)

    try:
      ShotgunORM.afterEntityCommit(self, batchDataCopy, sgBatchResult, sgCommitData, sgDryRun, sgCommitError)
    except Exception, e:
      if error == None:
        error = e

    if error != None:
      raise error

  def _beforeCommit(self, sgBatchData, sgCommitData, sgDryRun):
    '''
    Subclass portion of SgEntity.beforeCommit().

    ** The Entity is locked down when this is called **

    Args:
      * (dict) sgBatchData:
        Shotgun formatted batch dictionary of the Entities commit data.

      * (dict) sgCommitData:
        Dictionary used to pass data user between beforeCommit() and
        afterCommit().

      * (bool) sgDryRun:
        When True the commit is not updating Shotgun with any modifications,
        it is only in a test phase.
    '''

    pass

  def beforeCommit(self, sgBatchData, sgCommitData, sgDryRun):
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

      * (bool) sgDryRun:
        When True the commit is not updating Shotgun with any modifications,
        it is only in a test phase.
    '''

    ShotgunORM.LoggerEntity.debug('%(entity)s.beforeCommit()', {'entity': self})
    ShotgunORM.LoggerEntity.debug('    * sgBatchData: %(value)s', {'value': sgBatchData})
    ShotgunORM.LoggerEntity.debug('    * sgCommitData: %(value)s', {'value': sgCommitData})
    ShotgunORM.LoggerEntity.debug('    * sgDryRun: %(value)s', {'value': sgDryRun})

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
      self._beforeCommit(sgBatchData, sgCommitData, sgDryRun)
    except Exception, e:
      error = e

    batchDataCopy = copy.deepcopy(sgBatchData)

    try:
      ShotgunORM.beforeEntityCommit(self, batchDataCopy, sgCommitData, sgDryRun)
    except Exception, e:
      if error == None:
        error = e

    if error != None:
      raise error

  def _buildFields(self):
    '''
    Subclass portion of SgEntity.buildFields().
    '''

    pass

  def buildFields(self):
    '''
    Creates all the fields for the Entity.

    After _buildFields(...) has been called buildUserFields() is called.

    Note:
      This is called by the class factory after the Entity has been created and
      will immediately return anytime afterwards.
    '''

    # Only build the fields once!
    if self.__hasBuiltFields:
      return

    entityFieldInfos = self.schemaInfo().fieldInfos()

    self._fields['id'] = ShotgunORM.SgFieldID(
      entityFieldInfos.pop('id'),
      self
    )

    self._fields['type'] = ShotgunORM.SgFieldType(
      entityFieldInfos.pop('type'),
      self
    )

    fieldClasses = ShotgunORM.SgField.__fieldclasses__

    for fieldInfo in entityFieldInfos.values():
      fieldName = fieldInfo.name()

      fieldClass = fieldClasses.get(fieldInfo.returnType(), None)

      newField = fieldClass(None, sgFieldSchemaInfo=fieldInfo, sgEntity=self)

      if hasattr(self.__class__, fieldName):
        ShotgunORM.LoggerField.warn(
          'Entity type %(entity)s field name "%(name)s confilicts with class method of same name' % {
            'entity': self.schemaInfo().name(),
            'name': fieldName
          }
        )

      self._fields[fieldName] = newField

    self._buildFields()

    self.__hasBuiltFields = True

  def caching(self):
    '''
    Returns the caching state of the Entity.

    Values:
      -1: Caching is determined by the connections caching state (default)
      0: Disabled
      1: Enabled
    '''

    return self.__caching

  def clearCache(self):
    '''

    '''

    if self.isCaching():
      self.connection().clearCacheForEntity(self)

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

  def commit(self, sgFields=None, sgDryRun=False):
    '''
    Commits any modified Entity fields that have not yet been published to the
    Shotgun database.

    Returns True if anything modifcations were published to Shotgun.

    Args:
      * (dict) sgFields:
        List of fields to commit.  When specified only those fields will be
        commited.

      * (bool) sgDryRun:
        When True no field updates will be pushed to Shotgun.  Only the before
        and after commit calls will process.
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
        ],
        sgDryRun
      )

      return True

  def connection(self):
    '''
    Returns the SgConnection the Entity belongs to.
    '''

    return self.__sg_connection__()

  def delete(self, sgCommit=False, sgDryRun=False):
    '''
    Deletes the Entity from Shotgun.

    Args:
      * (bool) sgCommit:
        Deletes the Entity and immediately commits the change.
    '''

    with self:
      if not self.exists():
        raise RuntimeError('entity does not exist, can not generate request data for type delete')

      if sgCommit == False and sgDryRun == True:
        raise RuntimeError('cant dry run when sgCommit is False')

      if sgCommit:
        self.connection().delete(self, sgDryRun)
      else:
        self._markedForDeletion = True

  def disableCaching(self):
    '''
    Disables the caching of this Entity and only this Entity.

    To disable all caching for a Shotgun connection call the connections
    disableCaching() function.
    '''

    if self.isCaching():
      self.connection().clearCacheForEntity(self)

    self.__caching = 0

  def enableCaching(self):
    '''
    Enables the caching of this Entity and only this Entity.

    To enable all caching for a Shotgun connection call the connections
    enableCaching() function.
    '''

    self.__caching = 1

  def eventLogFilter(self):
    '''

    '''

    if not self.exists():
      return None

    return [
      [
        'entity',
        'is',
        self.toEntityFieldData()
      ]
    ]

    return

  def eventLogs(self, sgEventType=None, sgFields=None, sgRecordLimit=0):
    '''
    Returns the event log Entities for this Entity

    Args:
      * (str) sgEventType:
        Event type filter such as "Shotgun_Asset_Change".

      * (list) sgFields:
        List of fields to populate the results with.

      * (int) sgRecordLimit:
        Limits the amount of returned events.
    '''

    filters = self.eventLogFilter()

    if filters == None:
      return []

    connection = self.connection()

    order = [{'field_name':'created_at', 'direction':'desc'}]

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
      filters,
      sgFields,
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

    if not self.isBuildingFields():
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

        if fieldObj == None or fieldObj.returnType() not in sgReturnTypes:
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

  def fieldsInvalid(self, sgFields=None, sgReturnTypes=None, excludeWithSyncUpdate=True):
    '''
    Returns a list of field names that are not valid.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.

      * (bool) excludeWithSyncUpdate:
        When True fields that are not yet valid but have a pending sync update
        are considered valid.
    '''

    result = []

    with self:
      for name, field in self.fields(sgFields, sgReturnTypes).items():
        if field.isValid() or (excludeWithSyncUpdate and field.hasSyncUpdate()):
          continue

        result.append(name)

    result.sort()

    return result

  def fieldsWithCommit(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns a list of field names that have pending commits.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
    '''

    result = []

    # Bail early if the Entity does not have an ID or it is marked for deletion.
    if not self.exists():
      return result

    for field in self.fields(sgFields, sgReturnTypes).values():
      if field.hasCommit():
        result.append(field.name())

    return result

  def fieldsValid(self, sgFields=None, sgReturnTypes=None, includeWithSyncUpdate=True):
    '''
    Returns a list of field names that are valid.

    Args:
      * (list) sgFields:
        List of specific fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.

      * (bool) includeWithSyncUpdate:
        When True fields that are not yet valid but have a pending sync update
        are considered valid.
    '''

    result = []

    with self:
      for name, field in self.fields(sgFields, sgReturnTypes).items():
        if field.isValid() or (field.hasSyncUpdate() and includeWithSyncUpdate):
          result.append(name)

    result.sort()

    return result

  def fieldValues(self, sgFields=None, sgReturnTypes=None, sgSyncFields=None):
    '''
    Returns a dict containing the value of all specified fields.

    Use this function when you want to query multiple field values at once
    and perform the action in a single call to the Shotgun database.

    Args:
      * (list) sgFields:
        List of fields to return.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.

      * (dict) sgSyncFields:
        D of field names to populate any returned Entities with.
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
            result[field.name()] = field.value(sgSyncFields=sgSyncFields)
        finally:
          qEngine.unblock()

      return result

  def follow(self, sgUser):
    '''
    Configure the Shotgun HumanUser to follow this Entity.

    Returns True if successful.

    Args:
      * (SgEntity) sgUser:
        User which will follow the Entity.
    '''

    if (
      not self.exists() or
      sgUser['type'] != 'HumanUser' or
      not sgUser.exists()
    ):
      return False

    return self.connection().connection().follow(
      sgUser.toEntityFieldData(),
      self.toEntityFieldData()
    )['followed']

  def followers(self):
    '''
    Returns a list of user Entities that are following this Entity.
    '''

    if not self.exists():
      return []

    connection = self.connection()

    search = connection.connection().followers(self.toEntityFieldData())

    result = []

    if len(search) == 0:
      return result

    for i in search:
      result.append(
        connection._createEntity(
          i['type'],
          {
            'id': i['id'],
            'type': i['type']
          }

        )
      )

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

  def isBuildingFields(self):
    '''
    Returns True when the Entity is building its fields.
    '''

    return not self.__hasBuiltFields

  def isCaching(self):
    '''
    Returns True if the Entity will save its field values in the connections
    cache.

    Default returns the connections isCaching() state unless the Entity has
    has caching disabled by calling SgEntity.disableCaching().
    '''

    if self.__caching < 0:
      return self.connection().isCaching()
    else:
      return bool(self.__caching)

  def isCommitting(self):
    '''
    Returns True if the Entity is currently commiting to Shotgun.
    '''

    return self.__isCommitting

  def isCustom(self):
    '''
    Returns True if the Entity is a custom Shotgun entity, example CustomEntity01.
    '''

    return self.schemaInfo().isCustom()

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

    return self.schemaInfo().label()

  def lastEventLog(self, sgEventType=None, sgFields=None):
    '''
    Returns the last event log Entity for this field.

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

  def removeField(self, fieldName):
    '''
    Removes the specified use field from the Entity'
    '''

    with self:
      if not self.hasField(fieldName):
        raise RuntimeError('invalid field name "%s"' % fieldName)

      if not self.field(fieldName).isUserField():
        raise RuntimeError('unable to delete a non-user field')

      del self._fields[fieldName]

      # Because the field can still exist in another scope unset its parent!
      self.field(fieldName)._SgField__setParentEntity(None)

  def resetCaching(self):
    '''
    Resets the Entities caching state to that of the connections.
    '''

    with self:
      if self.__caching == -1:
        return

      self.__caching = -1

      self.connection().clearCacheForEntity(self)

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
        if (field.isValid() and ignoreValid) or (field.hasCommit() and ignoreWithUpdate):
          continue

        if field.invalidate():
          result = True

      return result

  def revive(self, sgDryRun=False):
    '''
    Revives the Entity.
    '''

    with self:
      if not self.exists():
        raise RuntimeError('entity does not exist, can not generate request data for type revive')

      self.connection().revive(self, sgDryRun)

  def schemaInfo(self):
    '''
    Returns the SgEntitySchemaInfo object that defines this Entity.
    '''

    return self.__classinfo__

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
        if backgroundPull:
          self.connection().queryEngine().addQueue(self, pullFields)
        else:
          values = self.valuesSg(pullFields)

          for field, value in values.items():
            fieldObj = self.field(field)

            fieldObj.setSyncUpdate(value)

            # Don't slow down the sync process by calling validate!
            #fieldObj.validate(forReal=False)

      if len(nonQueryableFields) >= 1:
        for field in nonQueryableFields:
          field.validate(forReal=True)

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

  def unfollow(self, sgUser):
    '''
    Configure the HumanUser to stop following this Entity.

    Returns True if successful.

    Args:
      * (SgEntity) sgUser:
        User that will will stop following the Entity.
    '''

    if (
      not self.exists() or
      not isinstance(sgUser, SgEntity) or
      sgUser['type'] != 'HumanUser' or
      not sgUser.exists()
    ):
      return False

    return self.connection().connection().unfollow(
      sgUser.toEntityFieldData(),
      self.toEntityFieldData()
    )['unfollowed']

  def valuesSg(self, sgFields=None, sgReturnTypes=None):
    '''
    Returns field values from Shotgun for the specified fields.

    Note:
      Fields which isQueryable() returns False will not be returned in the
      result!

    Args:
      * (list) sgFields:
        List of fields to fetch from Shotgun.

      * (list) sgReturnTypes:
        List of specific field return types to filter by.
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

    for fieldName, field in self.fields(sgFields, sgReturnTypes).items():
      if not field.isQueryable():
        continue

      pullFields.append(field.name())

    ShotgunORM.LoggerEntity.debug('    * pulling: %(sgFields)s', {'sgFields': pullFields})

    if len(pullFields) <= 0:
      return {}

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
