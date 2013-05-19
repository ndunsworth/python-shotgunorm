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

import threading
import webbrowser

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

# Fix for the lame ass return type "color2".  See ShotgunORM.SgFieldColor2 for more
# information on this lovely mess.
def _fixFieldSchema(sgEntityName, sgFieldSchemas):
  if not sgEntityName in ['Phase', 'Task']:
    return

  sgFieldSchemas['color']['data_type']['value'] = 'color2'

class SgEntityInfo(object):
  '''
  Class for representing basic information about a Shotgun Entity.
  '''

  def __repr__(self):
    if self.isCustom():
      return '<SgEntityInfo("%s"|"%s")>' % (self.name(), self.label())
    else:
      return '<SgEntityInfo("%s")>' % self.name()

  def __str__(self):
    return self.name()

  def __init__(self, name, label, fieldInfos):
    self._isCustom = name.startswith('CustomEntity') or name.startswith('CustomNonProjectEntity')
    self._name = str(name)
    self._label = str(label)
    self._fieldInfos = fieldInfos

  @classmethod
  def fromSg(self, sgEntityName, sgEntityLabel, sgFieldSchemas):
    '''
    Returns a new ShotgunORM.SgFieldInfo that is constructed from the arg "sgSchema".
    '''

    fieldInfos = {}

    _fixFieldSchema(sgEntityName, sgFieldSchemas)

    for fieldName, schemaData in sgFieldSchemas.items():
      if fieldName.startswith('step_'):
        continue

      fieldInfo = ShotgunORM.SgFieldInfo.fromSg(fieldName, schemaData)

      # Skip fields that have an unsupported return type!
      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        #print sgEntityName, fieldInfo.name(), schemaData
        #print '*' * 80
        continue

      fieldInfos[fieldName] = fieldInfo

    return self(sgEntityName, sgEntityLabel, fieldInfos)

  @classmethod
  def fromXML(self, sgXmlElement):
    '''
    From the passed XML data a new SgEntityInfo is returned.
    '''

    if sgXmlElement.tag != 'SgEntity':
      raise RuntimeError('invalid tag "%s"' % sgXmlElement.tag)

    entityFieldInfos = {}

    fields = sgXmlElement.find('fields')

    if fields == None:
      raise RuntimeError('could not find fields element')

    for field in fields:
      # Skip fields that have an unsupported return type!
      fieldInfo = ShotgunORM.SgFieldInfo.fromXML(field)

      if fieldInfo.returnType() == ShotgunORM.SgField.RETURN_TYPE_UNSUPPORTED:
        continue

      entityFieldInfos[field.attrib.get('name')] = fieldInfo

    entityName = sgXmlElement.attrib.get('name')
    entityLabel = sgXmlElement.attrib.get('label')

    return self(entityName, entityLabel, entityFieldInfos)

  def fieldInfo(self, sgField):
    '''
    Returns the SgFieldInfo for the field.
    '''

    return self._fieldInfos.get(sgField, None)

  def fieldInfos(self):
    '''
    Returns a list of ShotgunORM.SgFieldInfo objects used by the Entity.
    '''

    return dict(self._fieldInfos)

  def fields(self):
    '''
    Returns a list of field names.
    '''

    return sorted(self._fieldInfos.keys())

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

  # Set by the SgEntityClassFactory
  __classinfo__ = None

  __defaultentityclasses__ = {}

  @classmethod
  def registerDefaultEntityClass(self, sgEntityCls, sgEntityTypes):
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

      self.__defaultentityclasses__[e] = sgEntityCls

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
    try:
      field = self._fields[item]
    except KeyError:
      raise KeyError('invalid key field "%s"' % item)

    return field.value()

  def __setattr__(self, item, value):
    try:
      fieldObj = self._fields[item]
    except (AttributeError, KeyError) as e:
      return super(SgEntity, self).__setattr__(item, value)
    except:
      raise

    return  fieldObj.setValue(value)

  def __eq__(self, item):
    if isinstance(item, SgEntity):
      return self.type == item.type and self['id'] == item['id'] and \
        self.session().connection().url().lower() == item.session().connection().url().lower()
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

  def __int__(self):
    return self.id

  def __repr__(self):
    return '<%s>' % ShotgunORM.mkEntityString(self)

  def __init__(self, sgSession):
    self.__dict__['_fields'] = {}
    self._rlock = threading.RLock()
    self._session = sgSession
    self._markedForDeletion = False

    self._hasBuiltFields = False

  def _fetch(self, sgFields=[]):
    '''
    Internal function!

    Fetches the specified fields from the Shotgun db.

    Not thread safe!
    '''

    ####
    # DO NOT CALL THIS FUNCTION FOR SUMMARY FIELDS!
    ####

    if not self.exists():
      return

    connection = self.session().connection()
    sgconnection = connection.connection()

    queryFields = set([])

    for field in sgFields:
      fieldObj = self.field(field)

      if fieldObj == None:
        continue

      if fieldObj.isValid() or fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
        continue

      queryFields.add(field)

    # Bail if no fields need querying!
    if len(queryFields) <= 0:
      return

    queryFields = list(queryFields)

    ShotgunORM.LoggerEntity.debug('%(entity)s._fetch()', {'entity': self.__repr__()})
    ShotgunORM.LoggerEntity.debug('    * requested: %(sgFields)s', {'sgFields': sgFields})

    sgResult = sgconnection.find_one(self.type, self.toEntitySearchPattern(), queryFields)

    if sgResult == None:
      raise RuntimeError('unable to find Entity in Shotgun database %s' % self.__repr__())

    del sgResult['type']
    del sgResult['id']

    self._updateFields(sgResult)

  def _fromFieldData(self, sgData):
    '''
    Sets the Entities field values from data returned by a Shotgun query.

    This is called when the Entity object is created.
    '''

    self._lock()

    try:
      isNewEntity = not sgData.has_key('id')

      if isNewEntity:
        for field, value in sgData.items():
          fieldObj = self.field(field)

          # Skip expression summary fields.
          if fieldObj == None or fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
            continue

          fieldObj._fromFieldData(value)

          fieldObj._valid = True
          fieldObj._hasCommit = True
      else:
        for field, value in sgData.items():
          fieldObj = self.field(field)

          # Skip expression summary fields.
          if fieldObj == None or fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
            continue

          fieldObj._fromFieldData(value)

          fieldObj._valid = True
    finally:
      self._release()

  def _lock(self):
    '''
    Locks the Entity.
    '''

    self._rlock.acquire()

  def _release(self):
    '''
    Un-Locks the Entity.
    '''

    self._rlock.release()

  def _updateFields(self, sgData, setValue=True):
    '''
    Internal function!

    This is not thread safe do not call it!
    '''

    for field in sgData:
      fieldData = sgData[field]
      fieldObj = self.field(field)

      if fieldObj == None:
        raise RuntimeError('unable to find field "%s" on entity %s, this is most likely because the Entity schema has changed' % (field, self.__repr__()))

      # No need to do anythin for summary expression fields.
      if fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
        continue

      if setValue:
        fieldObj._fromFieldData(fieldData)

      fieldObj._valid = True
      fieldObj._hasCommit = False

  def buildFields(self):
    '''
    Builds the ShotgunORM.SgField objects for this Entity.

    Note:
    This is called by the class factory after the Entity has been created and
    will immediately return anytime afterwards.
    '''

    # Only build the fields once!
    if self._hasBuiltFields:
      return

    entityFieldInfos = self.info().fieldInfos().values()

    self._fields = {}

    for field in entityFieldInfos:
      fieldName = field.name()

      self._fields[fieldName] = field.create(self)

    self._hasBuiltFields = True

  def commit(self, sgFields=None):
    '''
    Commits any modified Entity fields that have not yet been published to the
    Shotgun database.

    Returns True if any fields were updated.

    Args:
      * (dict) sgFields:
        List of fields to commit.  When specified only those fields will be
        commited.
    '''

    self._lock()

    try:
      if self._markedForDeletion:
        result = self.delete(sgCommit=True)

        ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_DELETE)

        return result

      updateData = {}

      if sgFields == None:
        sgFields = self.fieldNames()
      elif isinstance(sgFields, str):
        sgFields = [sgFields]

      for field in sgFields:
        fieldObj = self.field(field)

        if fieldObj == None:
          raise RuntimeError('no field named "%s"' % field)

        if not fieldObj.hasUpdate():
          continue

        updateData[fieldObj.name()] = fieldObj.toFieldData()

      if len(updateData) <= 0:
        return False

      # Dont use the SgConnection, this is so if the Entity is being created
      # the ShotgunORM onEntityCreate callback isnt called.
      sgconnection = self.session().connection().connection()

      commitType = None

      if not self.exists():
        idField = self.field('id')

        sgResultId = sgconnection.create(self.type, updateData, ['id'])['id']

        idField._value = sgResultId
        idField._valid = True

        session = self.session()

        try:
          session._addEntity(self)
        except:
          pass

        commitType = ShotgunORM.COMMIT_TYPE_CREATE
      else:
        sgconnection.update(self.type, self['id'], updateData)

        commitType = ShotgunORM.COMMIT_TYPE_UPDATE

      self._updateFields(updateData, setValue=False)

      ShotgunORM.onEntityCommit(self, commitType)

      return True
    except:
      raise
    finally:
      self._release()

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

    sgData = {}

    if isinstance(inheritFields, str):
      inheritFields = [inheritFields]

    if len(inheritFields) >= 1:
      sgData.update(self.toFieldData(inheritFields))

    if sgData.has_key('id'):
      del sgData['id']

    if sgData.has_key('type'):
      del sgData['type']

    numberOfEntities = max(1, numberOfEntities)

    session = self.session()

    return self.session().create(self.type, sgData, sgCommit=False, numberOfEntities=numberOfEntities)

  def delete(self, sgCommit=False):
    '''
    Deletes the Entity from Shotgun.

    Args:
      * (bool) sgCommit:
        Deletes the Entity and immediately commits the change.
    '''

    return self.session().delete(self)

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

    session = self.session()

    filters = [
      ['entity', 'is', self.toEntityFieldData()],
    ]

    order = [{'field_name':'created_at','direction':'desc'}]

    if sgEventType != None:
      filters.append(['event_type', 'is', sgEventType])

    result = session.find('EventLogEntry', filters=filters, order=order, limit=sgRecordLimit)

    return result

  def exists(self):
    '''
    Returns True if the Entity has an ID and exists in the Shotgun database
    else returns False when the Entity has yet to be created with a commit.
    '''

    return self['id'] != None

  def field(self, sgField):
    '''
    Returns the Entity field.

    Args:
      * (str) sgField:
        Field name.
    '''

    return self._fields.get(sgField, None)

  def fieldLabels(self):
    '''
    Returns a list of the field labels associated with the Entity in Shotgun.
    '''

    result = []

    for field in self.fieldNames():
      result.append(self.field(field).label())

    return result

  def fieldNames(self):
    '''
    Returns a list of the field names associated with the Entity in Shotgun.
    '''

    return sorted(self.fields().keys())

  def fields(self):
    '''
    Returns a dict containing all ShotgunORM.SgField objects that belong to the
    Entity.
    '''

    return dict(self._fields)

  def fieldValues(self, sgFields=None):
    '''
    Returns a dict containing the value of all specified fields.

    This is useful when you want to query multiple fields at once and keep the
    outgoing Shotgun database calls to a minimum.

    Args:
      * (list) sgFields:
        List of fields to return.
    '''

    if sgFields == None:
      sgFields = self.fieldNames()
    else:
      if isinstance(sgFields, str):
        sgFields = [sgFields]
      elif not isinstance(sgFields, (list, set, tuple)):
        raise TypeError('expected a list for sgFields, got "%s"' % sgFields.__name__)

    sgFields = set(sgFields)

    self._lock()

    try:
      # First check if any fields are summary expression fields.
      # They may validate some of the other fields.
      expressionFields = []

      sgFields2 = []

      for field in sgFields:
        fieldObj = self.field(field)

        if fieldObj == None:
          raise RuntimeError('no field named "%s"' % field)

        if fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
          expressionFields.append(fieldObj)
        else:
          sgFields2.append(fieldObj)

      result = {}

      # Get the summary expression fields first!
      if len(expressionFields) >= 1:
        for field in expressionFields:
          result[field.name()] = field.value()

      sgconnection = self.session().connection().connection()

      queryFields = []

      exists = self.exists()

      for field in sgFields2:
        # If the field is valid use its value, if the Entity does not exist
        # use its default value.
        if field.isValid() or not exists:
          result[field.name()] = field.value()
        else:
          queryFields.append(field.name())

      if len(queryFields) >= 1:
        self._fetch(queryFields)

        for field in queryFields:
          result[field] = self.field(field).value()

      return result
    except:
      raise
    finally:
      self._release()

  def hasField(self, sgField):
    '''
    Returns True if the Entity contains the field specified.

    Args:
      * (str) sgField:
        Field name.
    '''

    return self._fields.has_key(sgField)

  def hasFieldUpdates(self):
    '''
    Returns True if any fields for the Entity have not yet been published to the
    Shotgun database.
    '''

    # Bail early if the Entity does not have an ID because it does yet exist
    # in the Shotgun db.
    if not self.exists():
      return True

    for field in self._fields.values():
      if field.hasUpdate():
        return True

    return False

  def info(self):
    '''
    Returns the SgEntityInfo object that defines this Entity.
    '''

    return self.__classinfo__

  def isCustom(self):
    '''
    Returns True if the Entity is a custom Shotgun entity, example CustomEntity01.
    '''

    return self.info().isCustom()

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

    session = self.session()

    filters = [
      ['entity', 'is', self.toEntityFieldData()],
    ]

    order = [{'field_name':'created_at','direction':'desc'}]

    if sgEventType != None:
      filters.append(['event_type', 'is', sgEventType])

    result = session.findOne('EventLogEntry', filters=filters, order=order)

    return result

  def revert(self, sgFields=None):
    '''
    Reverts any uncommited fields to their Shotgun db value.

    Returns True if any fields were invalidated else returns False.

    Args:
      * (list) sgFields:
        List of field names to revert.  When specified only those select fields
        will be reverted. All others will be left un-touched.
    '''

    self._lock()

    try:
      result = False

      if sgFields == None:
        sgFields = self.fieldNames()
      else:
        if isinstance(sgFields, str):
          sgFields = [sgFields]
        elif not isinstance(sgFields, (list, set, tuple)):
          raise TypeError('expected a list for sgFields, got "%s"' % sgFields.__name__)

      for field in sgFields:
        fieldObj = self.field(field)

        if fieldObj == None:
          continue

        if not fieldObj.hasUpdate():
          continue

        fieldObj.invalidate()

        result = True

      return result
    except:
      raise
    finally:
      self._release()

  def revive(self):
    '''
    Revives the Entity.
    '''

    return self.session().revive(self)

  def session(self):
    '''
    Returns the SgSession the Entity belongs to.
    '''

    return self._session

  def sync(self, sgFields=None):
    '''
    Syncs the Entity with Shotgun so future calls to field values re-query the
    Shotgun database.  Immediately returns if the Entity doesn't exist in Shotgun.

    Returns True if any fields were set to sync.

    Args:
      * (list) sgFields:
        List of field names to sync.  When specified only those select fields
        will be synced.
    '''

    self._lock()

    try:
      if not self.exists():
        return False

      if sgFields == None or sgFields == []:
        count = 0

        for field in self._fields.values():
          fieldName = field.name()

          # Do NOT invalidate the id field!
          if fieldName == 'id' or field.hasUpdate():
            continue

          field.invalidate()

          count += 1

        return count >= 1
      else:
        count = 0

        if isinstance(sgFields, str):
          sgFields = [sgFields]
        elif not isinstance(sgFields, (list, set, tuple)):
          raise TypeError('expected a list for sgFields, got "%s"' % sgFields.__name__)

        sgFields = set(sgFields)

        for field in sgFields:
          fieldObj = self.field(field)

          if fieldObj == None or field == 'id' or fieldObj.hasUpdate():
            continue

          fieldObj.invalidate()

          count += 1

        return count >= 1
    except:
      raise
    finally:
      self._release()

  def toBatchFieldData(self):
    '''
    Returns the Shotgun formatted dict of the Entity that would be used in a
    SgSession.batch() submit.

    Returns None if the Entity has nothing for batch.
    '''

    if self._markedForDeletion:
      if not self.exists():
        raise RuntimeError('entity does not exist, can not generate request data for type delete')

      result = {
        'request_type': 'delete',
        'entity_type': self.type,
        'entity_id': self['id']
      }

      return result

    data = self.toFieldUpdateData()

    if len(data) <= 0:
      return None

    result = None

    if not self.exists():
      result = {
        'request_type': 'create',
        'entity_type': self.type,
        'data': data
      }
    else:
      result = {
        'request_type': 'update',
        'entity_type': self.type,
        'entity_id': self['id'],
        'data': data
      }

    return result

  def toEntityFieldData(self):
    '''
    Retruns a Shotgun formatted dict search pattern used for the field value
    of another Entities search pattern.
    '''

    if not self.exists():
      raise RuntimeError('can not build field pattern for an un-commited Entity')

    return {'type': self.type, 'id': self['id']}

  def toEntitySearchPattern(self):
    '''
    Returns a Shotgun formatted search pattern that can be used to find this
    Entity in a find() and findOne() call.
    '''

    return [['id', 'is', self['id']]]

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
    else:
      if isinstance(sgFields, str):
        sgFields = [sgFields]
      elif not isinstance(sgFields, (list, set, tuple)):
        raise TypeError('expected a list for sgFields, got "%s"' % sgFields.__name__)

    sgFields = set(sgFields)

    result = {}

    if len(sgFields) <= 0:
      return result

    # First check if any fields are summary expression fields.
    # They may validate some of the other fields.
    expressionFields = []

    sgFields2 = []

    for field in sgFields:
      fieldObj = self.field(field)

      if fieldObj == None:
        raise RuntimeError('no field named "%s"' % field)

      if fieldObj.returnType() == ShotgunORM.SgField.RETURN_TYPE_SUMMARY:
        expressionFields.append(fieldObj)
      else:
        sgFields2.append(fieldObj)

    # Get the summary expression fields first!
    if len(expressionFields) >= 1:
      for field in expressionFields:
        result[field.name()] = field.toFieldData()

    sgconnection = self.session().connection().connection()

    queryFields = []

    exists = self.exists()

    for field in sgFields2:
      # If the field is valid use its value, if the Entity does not exist
      # use its default value.
      if field.isValid() or not exists:
        result[field.name()] = field.toFieldData()
      else:
        queryFields.append(field.name())

    if len(queryFields) >= 1:
      self._fetch(queryFields)

      for field in queryFields:
        result[field] = self.field(field).toFieldData()

    return result

  def toFieldUpdateData(self, sgFields=None):
    '''
    Returns the field data of all fields which contain a pending commit as a
    Shotgun formatted dict.

    Returns an empty dict when no fields contain a pending commit.

    Args:
      * (list) sgFields:
        List of field names to sync.  When specified only those select fields
        will be returned.
    '''

    if sgFields == None:
      sgFields = self.fieldNames()
    else:
      if isinstance(sgFields, str):
        sgFields = [sgFields]
      elif not isinstance(sgFields, (list, set, tuple)):
        raise TypeError('expected a list for sgFields, got "%s"' % sgFields.__name__)

    sgFields = set(sgFields)

    result = {}

    if len(sgFields) <= 0:
      return result

    for field in sgFields:
      fieldObj = self.field(field)

      if fieldObj == None:
        raise RuntimeError('no field named "%s"' % field)

      if fieldObj.hasUpdate():
        result[field] = fieldObj.toFieldData()

    return result

  @property
  def type(self):
    '''
    Returns the Entities type.
    '''

    return self.info().name()

  def webUrl(self, openInBrowser=False):
    '''
    Returns the Shotgun URL of the Entity.

    Args:
      * (bool) openInBrowser:
        When True the Entities URL will be opened in the operating systems
        default web-browser.
    '''

    id = self['id']

    url = self.session().connection().url()

    if id == None:
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
      url += '/detail/%s/%d' % (self.type, self['id'])

    if openInBrowser:
      webbrowser.open(url)

    return url
