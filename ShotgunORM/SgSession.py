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
  'SgSession',
  'SgSessionCached'
]

# Python imports
import threading

# This module imports
import ShotgunORM

class SgSession(object):
  '''
  SgConnection session Class.
  '''

  def __repr__(self):
    return '<SgSession("%s")>' % self.name()

  def __init__(self, sgConnection, sgSessionName):
    self._connection = sgConnection
    self._name = sgSessionName

  def _createEntity(self, sgEntityType, sgData, sgFields=None):
    '''
    Internal function!

    Do not call!
    '''

    ShotgunORM.LoggerSession.debug('%(session)s._createEntity(...)', {'session': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * sgEntityType: %(entityName)s', {'entityName': sgEntityType})
    ShotgunORM.LoggerSession.debug('    * sgData: %(sgData)s', {'sgData': sgData})
    ShotgunORM.LoggerSession.debug('    * sgFields: %(sgFields)s', {'sgFields': sgFields})

    sgData = dict(sgData)

    factory = self.connection().classFactory()

    if not sgFields in [None, []]:
      sgSearch = self.connection().connection().find_one(sgEntityType, [['id', 'is', sgData['id']]], sgFields)

      if sgSearch == None:
        raise RuntimError('unable to locate Entity in Shotgun')

      sgData.update(sgSearch)

      return factory.createEntity(self, sgEntityType, sgData)
    else:
      return factory.createEntity(self, sgEntityType, sgData)

  def _createEntities(self, sgEntities):
    '''
    Internal function!

    Do not call!
    '''

    result = []

    if len(sgEntities) <= 0:
      return result

    connection = self.connection()
    sgconnection = connection.connection()

    entities = {}

    index = 0

    for e in sgEntities:
      t = e['type']

      if not entities.has_key(t):
        entities[t] = {
          'ids': [],
          'indices': {}
        }

      iD = e['id']

      entities[t]['ids'].append(iD)
      entities[t]['indices'][iD] = index

      index += 1

    result = [None] * len(sgEntities)

    ShotgunORM.LoggerSession.debug('%(session)s._createEntities(...)', {'session': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * Entities: %(entities)s', {'entities': sgEntities})

    for key, value in entities.items():
      ShotgunORM.LoggerSession.debug('        * Entity: %(entityName)s', {'entityName': key})
      ShotgunORM.LoggerSession.debug('        * ids: %(ids)s', {'ids': value['ids']})

      sgSearch = sgconnection.find(
        key,
        [['id', 'in', value['ids']]],
        list(connection.defaultEntityQueryFields(key)),
      )

      if len(sgSearch) != len(value['ids']):
        raise RuntimeError('one or more Entities not found in Shotgun')

      indices = value['indices']

      for e in sgSearch:
        entity = self._createEntity(key, e)

        index = indices[entity.id]

        result[index] = entity

    return result

  def _flattenFilters(self, sgFilters):
    '''
    Internal function used to flatten Shotgun filter lists.  This will convert
    SgEntity objects into their equivalent Shotgun search pattern.

    Example:
    myProj = myConnection.findOne('Project', [['id', 'is', 65]])
    randomAsset = myConnection.findOne('Asset', [['project', 'is', myProj]])

    sgFilters becomes [['project', 'is', {'type': 'Project', 'id': 65}]]
    '''

    def flattenDict(obj):
      result = {}

      for key, value in obj.items():
        if isinstance(value, ShotgunORM.SgEntity):
          result[key] = value.toEntityFieldData()
        elif isinstance(value, ShotgunORM.SgField):
          result[key] = value.toFieldData()
        elif isinstance(value, (list, set, tuple)):
          result[key] = flattenList(value)
        elif isinstance(value, dict):
          result[key] = flattenDict(value)
        else:
          result[key] = value

      return result

    def flattenList(obj):
      result = []

      for i in obj:
        if isinstance(i, ShotgunORM.SgEntity):
          result.append(i.toEntityFieldData())
        elif isinstance(i, ShotgunORM.SgField):
          result.append(i.toFieldData())
        elif isinstance(i, (list, set, tuple)):
          result.append(flattenList(i))
        elif isinstance(i, dict):
          result.append(flattenDict(i))
        else:
          result.append(i)

      return result

    if sgFilters == None or sgFilters == []:
      return []

    if isinstance(sgFilters, int):
      return [['id', 'is', sgFilters]]
    elif isinstance(sgFilters, (list, set, tuple)):
      return flattenList(sgFilters)
    elif isinstance(sgFilters, dict):
      return flattenDict(sgFilters)
    else:
      return sgFilters

  def batch(self, requests):
    '''
    Make a batch request of several create, update, and/or delete calls at one
    time. This is for performance when making large numbers of requests, as it
    cuts down on the overhead of roundtrips to the server and back. All requests
    are performed within a transaction, and if any request fails, all of them
    will be rolled back.
    '''

    sgBatchRequests = []
    sgBatchRequestEntities = []

    batchResult = []

    # Try here because we will be locking the entities down.  If anything fails
    # unlock the ones we've already processed and then raise
    try:
      for entity in requests:
        entity._lock()

        entityBatchData = entity.toBatchFieldData()

        if entityBatchData == None:
          batchResult.append([entity, None])

          entity._release()

          continue

        batchResult.append([entity, entityBatchData])

        sgBatchRequests.append(entityBatchData)
        sgBatchRequestEntities.append(entity)

      if len(sgBatchRequests) <= 0:
        return batchResult

      sgconnection = self.connection().connection()

      sgBatchResult = sgconnection.batch(sgBatchRequests)
      sgBatchResultIter = iter(sgBatchResult)

      for entity, request, result in map(None, sgBatchRequestEntities, sgBatchRequests, sgBatchResult):
        requestType = request['request_type']

        if requestType == 'delete':
          entity._markedForDeletion = False

          ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_DELETE)
        elif requestType == 'create':
          del result['type']

          entity._updateFields(result)

          # For cached sessions.
          try:
            self._addEntity(entity)
          except:
            pass

          ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_CREATE)
        elif requestType == 'update':
          del result['type']
          del result['id']

          entity._updateFields(result)

          ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_UPDATE)
    finally:
      for entity in sgBatchRequestEntities:
        entity._release()

    return batchResult

  def connection(self):
    '''
    Returns the SgConnection the session belongs to.
    '''

    return self._connection

  def create(self, sgEntityType, sgData={}, sgCommit=False, numberOfEntities=1):
    '''
    Creates a new Entity and returns it.  The returned Entity does not exist in
    the Shotgun database.

    Args:
      * (dict) sgData:
        Shotgun formated dictionary of field data.
    '''

    ShotgunORM.LoggerSession.debug('%(session)s.create(...)', {'session': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * sgEntityType: %(entityName)s', {'entityName': sgEntityType})
    ShotgunORM.LoggerSession.debug('    * sgData: %(sgData)s', {'sgData': sgData})
    ShotgunORM.LoggerSession.debug('    * sgCommit: %(sgCommit)s', {'sgCommit': sgCommit})

    factory = self.connection().classFactory()

    numberOfEntities = max(1, numberOfEntities)

    sgData = self._flattenFilters(sgData)

    if numberOfEntities == 1:
      newEntity = self._createEntity(sgEntityType, sgData)

      if sgCommit:
        newEntity.commit()

      return newEntity
    else:
      result = []

      for n in range(0, numberOfEntities):
        newEntity = self._createEntity(sgEntityType, sgData)

        result.append(newEntity)

      if sgCommit:
        self.batch(result)

      return result

  def delete(self, sgEntity):
    '''
    Deletes the passed Entity from Shotgun.

    Args:
      * (SgEntity) sgEntity:
        Entity to delete.
    '''

    sgEntity._lock()

    try:
      if not sgEntity.exist():
        raise RuntimeError('unable to delete a node which does not exist in Shotgun')

      result = self.connection().connection().delete(sgEntity.type, sgEntity['id'])
    finally:
      sgEntity._release()

    if result:
      ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_UPDATE)

    return result

  def find(
    self,
    entity_type,
    filters,
    fields=None,
    order=None,
    filter_operator=None,
    limit=0,
    retired_only=False,
    page=0
  ):
    '''
    Find entities.

    Args:
      * (str) entity_type:
        Entity type to find.

      * (list) filters:
        List of Shotgun formatted filters.

      * (list) fields:
        Fields that return results will have filled in with data from Shotgun.

      * (list) order:
        List of Shotgun formatted order filters.

      * (str) filter_operator:
        Controls how the filters are matched. There are only two valid
        options: all and any. You cannot currently combine the two options in the
        same query.

      * (int) limit:
        Limits the amount of Entities can be returned.

      * (bool) retired_only:
        Return only retired entities.

      * (int) page:
        Return a single specified page number of records instead of the entire
        result set
    '''

    connection = self.connection()
    sgconnection = connection.connection()
    schema = connection.schema()

    entity_type = schema.entityApiName(entity_type)
    filters = self._flattenFilters(filters)

    if fields == None:
      fields = list(connection.defaultEntityQueryFields(entity_type))
    else:
      if isinstance(fields, str):
        fields = [fields]

      fields = set(fields)

      if 'default' in fields:
        fields.discard('default')

        fields.update(connection.defaultEntityQueryFields(entity_type))

      fields = list(fields)

    ShotgunORM.LoggerSession.debug('%(sgSession)s.find(...)', {'sgSession': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * entity_type: %(entityType)s', {'entityType': entity_type})
    ShotgunORM.LoggerSession.debug('    * filters: %(sgFilters)s', {'sgFilters': filters})
    ShotgunORM.LoggerSession.debug('    * fields: %(sgFields)s', {'sgFields': fields})

    searchResult = sgconnection.find(
      entity_type=entity_type,
      filters=filters,
      fields=fields,
      order=order,
      filter_operator=filter_operator,
      limit=limit,
      retired_only=retired_only,
      page=page
    )

    if searchResult != None:
      newResult = []

      for i in searchResult:
        entity = self._createEntity(entity_type, i)

        newResult.append(entity)

      searchResult = newResult

    return searchResult

  def findOne(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
  ):
    '''
    Find one entity. This is a wrapper for find() with a limit=1. This will also
    speeds the request as no paging information is requested from the server.
    '''

    connection = self.connection()
    sgconnection = connection.connection()
    schema = connection.schema()

    entity_type = schema.entityApiName(entity_type)
    filters = self._flattenFilters(filters)

    if fields == None:
      fields = list(connection.defaultEntityQueryFields(entity_type))
    else:
      if isinstance(fields, str):
        fields = [fields]

      fields = set(fields)

      if 'default' in fields:
        fields.discard('default')

        fields.update(connection.defaultEntityQueryFields(entity_type))

      fields = list(fields)

    ShotgunORM.LoggerSession.debug('%(sgSession)s.findOne(...)', {'sgSession': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * entity_type: %(entityType)s', {'entityType': entity_type})
    ShotgunORM.LoggerSession.debug('    * filters: %(sgFilters)s', {'sgFilters': filters})
    ShotgunORM.LoggerSession.debug('    * fields: %(sgFields)s', {'sgFields': fields})

    searchResult = sgconnection.find_one(
      entity_type=entity_type,
      filters=filters,
      fields=fields,
      order=order,
      filter_operator=filter_operator,
      retired_only=retired_only
    )

    if searchResult != None:
      return self._createEntity(entity_type, searchResult)
    else:
      return None

  def name(self):
    '''
    Returns the name of the SgSession.
    '''

    return self._name

  def revive(self, sgEntity):
    '''
    Revives (un-deletes) the Entity matching entity_type and entity_id.

    Args:
      * (SgEntity) sgEntity
        Entity to revive
    '''

    sgconnection = self.connection().connection()

    result = sgconnection.revive(sgEntity.type, sgEntity['id'])

    if result:
      ShotgunORM.onEntityCommit(self, ShotgunORM.COMMIT_TYPE_REVIVE)

    return result

  def schemaChanged(self):
    '''
    This is called when the parent SgConnection's schema has been updated.

    Subclasses of SgSession that cache Entities should invalidate their internal
    cache when this is called.
    '''

    return

  def search(self, sgEntityType, sgSearchExp, sgFields=None, sgSearchArgs=[], order=None, limit=0, retired_only=False, page=0, onlyOne=False):
    '''
    Uses a search string to find entities in Shotgun instead of a list.

    For more information on the search syntax check the ShotgunORM documentation.

    Args:
      * (str) sgEntityType:
        Entity type to find.

      * (str) sgSearchExp:
        Search expression string.

      * (list) sgFields:
        Fields that return results will have filled in with data from Shotgun.

      * (list) sgSearchArgs:
        Args used by the search expression string during evaluation.

      * (list) order:
        List of Shotgun formatted order filters.

      * (int) limit:
        Limits the amount of Entities can be returned.

      * (bool) retired_only:
        Return only retired entities.

      * (int) page:
        Return a single specified page number of records instead of the entire
        result set

      * (bool) onlyOne:
        Return only one result.
    '''

    connection = self.connection()
    sgconnection = connection.connection()

    entity_type = connection.schema().entityApiName(sgEntityType)

    ShotgunORM.LoggerSession.debug('%(sgSession)s.search(...)', {'sgSession': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * entity_type: %(entityType)s', {'entityType': entity_type})
    ShotgunORM.LoggerSession.debug('    * search_exp: "%(sgSearchExp)s"', {'sgSearchExp': sgSearchExp})
    ShotgunORM.LoggerSession.debug('    * fields: %(sgFields)s', {'sgFields': sgFields})

    filters = ShotgunORM.parseToLogicalOp(
      connection.schema().entityInfo(entity_type),
      sgSearchExp,
      sgSearchArgs
    )

    filters = self._flattenFilters(filters)

    if sgFields == None:
      sgFields = list(connection.defaultEntityQueryFields(entity_type))
    else:
      if isinstance(sgFields, str):
        fields = [sgFields]

      sgFields = set(sgFields)

      if 'default' in sgFields:
        sgFields.discard('default')

        sgFields.update(connection.defaultEntityQueryFields(entity_type))

    searchResult = None

    if onlyOne:
      searchResult = sgconnection.find_one(
        entity_type,
        filters,
        sgFields,
        order=order,
        retired_only=retired_only,
      )
    else:
      searchResult = sgconnection.find(
        entity_type,
        filters,
        sgFields,
        order=order,
        limit=limit,
        retired_only=retired_only,
        page=page
      )

    if searchResult != None:
      if onlyOne:
        return self._createEntity(entity_type, searchResult)
      else:
        newResult = []

        for i in searchResult:
          entity = self._createEntity(entity_type, i)

          newResult.append(entity)

        searchResult = newResult

    return searchResult

  def searchOne(self, sgEntityType, sgSearchExp, sgFields=None, sgSearchArgs=[], order=None, retired_only=False, page=0):
    '''
    Same as search(...) but only returns a single Entity.
    '''

    result = self.search(sgEntityType, sgSearchExp, sgFields, sgSearchArgs, order=order, limit=1, retired_only=retired_only, page=page)

    if len(result) >= 1:
      return result[0]

    return None

class SgSessionCached(SgSession):
  '''
  SgConnection cached session Class.
  '''

  def __init__(self, sgConnection, sgSessionName):
    super(SgSessionCached, self).__init__(sgConnection, sgSessionName)

    self._lockCache = threading.RLock()

    self._entityCache = {}

  def _addEntity(self, sgEntity):
    '''
    Internal function!

    Used by SgEntities and SgSessions when they commit a new Entity to Shotgun.
    '''

    self._lockCache.acquire()

    try:
      entityType = sgEntity.type

      del self._entityCache[entityType][-1][id(sgEntity)]

      self._entityCache[entityType][sgEntity['id']] = sgEntity
    finally:
      self._lockCache.release()

  def _createEntity(self, sgEntityType, sgData, sgFields=None):
    '''
    Internal function!

    Locks the session and if the Entity has an ID the cache is checked to see if
    it already has an SgEntity and if so it returns it otherwise it creates one.
    '''

    ShotgunORM.LoggerSession.debug('%(session)s._createEntity(...)', {'session': self.__repr__()})
    ShotgunORM.LoggerSession.debug('    * sgEntityType: %(entityName)s', {'entityName': sgEntityType})
    ShotgunORM.LoggerSession.debug('    * sgData: %(sgData)s', {'sgData': sgData})
    ShotgunORM.LoggerSession.debug('    * sgFields: %(sgFields)s', {'sgFields': sgFields})

    sgData = dict(sgData)

    factory = self.connection().classFactory()

    self._lockCache.acquire()

    try:
      eId = None

      if not sgData.has_key('id'):
        eId = -1
      else:
        eId = int(sgData['id'])

      result = None

      if not self._entityCache.has_key(sgEntityType):
        self._entityCache[sgEntityType] = {
          -1: {}
        }

      if eId <= -1:
        result = factory.createEntity(self, sgEntityType, sgData)

        self._entityCache[sgEntityType][-1][id(result)] = result
      else:
        if self._entityCache[sgEntityType].has_key(eId):
          result = self._entityCache[sgEntityType][eId]

          result._lock()

          try:
            for field in dict(sgData):
              fieldObj = result.field(field)

              if fieldObj == None or fieldObj.isValid():
                del sgData[field]

            if len(sgData) >= 1:
              result._updateFields(sgData)
          finally:
            result._release()
        else:
          result = factory.createEntity(self, sgEntityType, sgData)

          self._entityCache[sgEntityType][eId] = result

        if not sgFields in [None, []]:
          result._lock()

          try:
            queryFields = []

            for field in sgFields:
              fieldObj = result.field(field)

              if fieldObj == None or fieldObj.isValid():
                continue

              queryFields.append(field)

            if len(queryFields) >= 1:
              ShotgunORM.LoggerSession.debug('    * pulled: %(sgFields)s', {'sgFields': sgFields})

              sgSearch = self.connection().connection().find_one(sgEntityType, [['id', 'is', result.id]], sgFields)

              if sgSearch == None:
                raise RuntimError('unable to locate Entity in Shotgun')

              del sgSearch['type']
              del sgSearch['id']

              result._updateFields(sgSearch)
          finally:
            result._release()
    finally:
      self._lockCache.release()

    return result

  def _createEntities(self, sgEntities):
    '''
    Internal function!

    Do not call!
    '''

    self._lockCache.acquire()

    try:
      if len(sgEntities) <= 0:
        return []

      result = [None] * len(sgEntities)

      connection = self.connection()
      sgconnection = connection.connection()

      entities = {}

      index = 0

      for e in sgEntities:
        iD = e['id']
        t = e['type']

        if not entities.has_key(t):
          entities[t] = {
            'ids': [],
            'indices': {},
            'fields': list(connection.defaultEntityQueryFields(t))
          }

        iD = e['id']

        ids = entities[t]['ids']
        indices = entities[t]['indices']

        if self._entityCache.has_key(t):
          if self._entityCache[t].has_key(iD):
            eObj = self._entityCache[t][iD]

            noPull = True

            for field in entities[t]['fields']:
              if not eObj.field(field).isValid():
                noPull = False

                break

            if noPull:
              result[index] = eObj
            else:
              ids.append(iD)

              indices[iD] = index
          else:
            ids.append(iD)

            indices[iD] = index
        else:
          ids.append(iD)

          indices[iD] = index

        index += 1

      ShotgunORM.LoggerSession.debug('%(session)s._createEntities(...)', {'session': self.__repr__()})
      ShotgunORM.LoggerSession.debug('    * Entities: %(entities)s', {'entities': sgEntities})

      for key, value in entities.items():
        if len(value['ids']) <= 0:
          continue

        if key in ['AppWelcome', 'Banner']:
          for n in value['ids']:
            entity = self._createEntity(key, {'id': n})

            index = indices[entity.id]

            result[index] = entity

          continue

        ShotgunORM.LoggerSession.debug('        * Entity: %(entityName)s', {'entityName': key})
        ShotgunORM.LoggerSession.debug('        * ids: %(ids)s', {'ids': value['ids']})

        sgSearch = sgconnection.find(
          key,
          [['id', 'in', value['ids']]],
          list(connection.defaultEntityQueryFields(key)),
        )

        if len(sgSearch) != len(value['ids']):
          raise RuntimeError('one or more Entities not found in Shotgun')

        indices = value['indices']

        for e in sgSearch:
          entity = self._createEntity(key, e)

          index = indices[entity.id]

          result[index] = entity

      return result

    finally:
      self._lockCache.release()

  def clearCache(self, sgEntityTypes=None):
    '''
    Clears all cached Entities.

    Args:
      * (list) sgEntityTypes:
        List of Entity types to clear.
    '''

    self._lockCache.acquire()

    try:
      if sgEntityTypes == None:
        self._entityCache = {}
      else:
        if isinstance(sgEntityTypes, str):
          sgEntityTypes = [sgEntityTypes]

        for i in sgEntityTypes:
          if self._entityCache.has_key(i):
            del self._entityCache[i]

      self._lockCache.release()
    except:
      self._lockCache.release()

      raise

  def findOne(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
  ):
    '''
    Find one entity. This is a wrapper for find() with a limit=1. This will also
    speeds the request as no paging information is requested from the server.
    '''

    if isinstance(filters, int):
      entity_type = self.connection().schema().entityApiName(entity_type)

      if self._entityCache.has_key(entity_type):
        iD = filters

        if self._entityCache[entity_type].has_key(iD):
          return self._createEntity(entity_type, {'id': iD}, fields)

    return super(SgSessionCached, self).findOne(
      entity_type,
      filters,
      fields,
      order,
      filter_operator,
      retired_only,
    )

  def schemaChanged(self):
    '''
    This is called when the parent SgConnection's schema has been updated.

    Subclasses of SgSession that cache Entities should invalidate their internal
    cache when this is called.
    '''

    self._lockCache.acquire()

    self._entityCache = {}
