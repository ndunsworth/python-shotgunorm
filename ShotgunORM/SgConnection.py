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
  'SgConnection'
]

# Python imports
import copy
import os
import threading
import types
import weakref
import webbrowser

# This module imports
import ShotgunORM

class SgConnectionMeta(type):
  '''
  Singleton metaclass for SgSchema objects.
  '''

  __lock__ = threading.Lock()
  __connections__ = {}

  def __new__(cls, name, bases, dct):
    update = dict(dct)

    update['__connections__'] = {}

    return super(SgConnectionMeta, cls).__new__(cls, name, bases, update)

  def __call__(cls, *args, **kwargs):
    with SgConnectionMeta.__lock__:
      result = super(SgConnectionMeta, cls).__call__(*args, **kwargs)

      urlLower = result.url().lower()

      classConnections = cls.__connections__

      login = result.login()
      key = result.key()

      try:
        ref = classConnections[urlLower][login][key]

        refResult = ref()

        if refResult != None:
          return refResult
      except KeyError:
        pass

      resultWeak = weakref.ref(result)

      if not classConnections.has_key(urlLower):
        classConnections[urlLower] = {
          login: {
            key: resultWeak
          }
        }
      elif not classConnections[urlLower].has_key(login):
        classConnections[urlLower][login] = {
          key: resultWeak
        }
      else:
        classConnections[urlLower][login][key] = resultWeak

      allConnections = SgConnectionMeta.__connections__

      if not allConnections.has_key(urlLower):
        allConnections[urlLower] = weakref.WeakValueDictionary()

      allConnections[urlLower][id(result)] = result

      # Initialize!
      schema = result.schema()

      if not schema.isInitialized():
        schema.initialize(result)
      else:
        factory = result.classFactory()

        factory.initialize()

      result.queryEngine().start()

      return result

  @classmethod
  def connections(cls, url):
    '''
    Returns all the active SgConnection objects for a given URL string.
    '''

    url = url.lower()

    if not SgConnectionMeta.__connections__.has_key(url):
      return []

    return SgConnectionMeta.__connections__[url].values()

class SgConnectionPriv(object):
  '''
  Private base class for Shotgun connections.

  This class is a wrapper to the Shotgun Python API.
  '''

  __metaclass__ = SgConnectionMeta

  def __init__(self, url, login, key):
    self._url = str(url)
    self._login = str(login)
    self._key = str(key)

    self._connection = ShotgunORM.SHOTGUN_API.shotgun.Shotgun(
      self._url,
      self._login,
      self._key,
      connect=False
    )

  def _sg_batch(self, requests):
    '''
    Calls the Shotgun Python API batch function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().batch(requests)

  def _sg_delete(self, entityType, entityId):
    '''
    Calls the Shotgun Python API delete function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().delete(entityType, entityId)

  def _sg_find(
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
    Calls the Shotgun Python API find function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      if fields != None:
        fields = list(fields)

      return self.connection().find(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        limit,
        retired_only,
        page
      )

  def _sg_find_one(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
  ):
    '''
    Calls the Shotgun Python API find_one function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      if fields != None:
        fields = list(fields)

      return self.connection().find_one(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        retired_only,
      )

  def _sg_revive(self, entityType, entityId):
    '''
    Calls the Shotgun Python API revive function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().revive(entityType, entityId)

  def connect(self):
    '''
    Connects to the Shotgun db.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      self.connection().connect()

  def connection(self):
    '''
    Returns the Shotgun connection object.
    '''

    return self._connection

  def disconnect(self):
    '''
    Closes the connection to Shotgun.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      self.connection().close()

  def isConnected(self):
    '''
    Returns True if the connection is connected to the Shotgun db.
    '''

    return self.connection()._connection != None

  def key(self):
    '''
    Returns the Shotgun key for the connection.
    '''

    return self._key

  def login(self):
    '''
    Returns the Shotgun login for the connection.
    '''

    return self._login

  def url(self, openInBrowser=False):
    '''
    Returns the Shotgun url for the connection.

    Args:
      * (bool) openInBrowser:
        When True opens the URl in the operating systems default web-browser.
    '''

    if openInBrowser:
      webbrowser.open(self._url)

    return self._url

class SgConnection(SgConnectionPriv):
  '''
  Class that represents a connection to Shotgun.

  This class is a singleton for a given url/login/key so multiple calls of
  the same info return the same SgConnection.
  '''

  def __repr__(self):
    return '<%s(url:"%s", login:"%s")>' % (self.__class__.__name__, self.url(), self.login())

  #def __eq__(self, item):
  #  if not isinstance(item, SgConnection):
  #    return False
  #
  #  return (self.key() == item.key() and self.url() == item.url())
  #
  #def __ne__(self, item):
  #  return not (self == item)

  def __enter__(self):
    self.__lockCache.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lockCache.release()

  def __init__(self, url, login, key):
    super(SgConnection, self).__init__(url, login, key)

    self.__lockCache = threading.RLock()

    self._fieldQueryDefaults = 'default'
    self._fieldQueryDefaultsFallback = 'default'

    self.__qEngine = ShotgunORM.SgQueryEngine(self)
    self.__schema = ShotgunORM.SgSchema.createSchema(self._url)
    self._factory = ShotgunORM.SgEntityClassFactory(self)

    self.__entityCache = {}
    self.__entityCaching = True

  def _addEntity(self, sgEntity):
    '''
    Internal function!

    Used by SgEntities and SgConnections when they commit a new Entity to Shotgun.
    '''

    with self:
      self.__entityCache[sgEntity.type][sgEntity['id']] = {
        'entity': weakref.ref(sgEntity),
        'cache': {}
      }

  def _cacheEntity(self, sgEntity):
    '''
    Internal function!

    Caches the passed Entities field values.

    Only fields that contain no commit update and are either valid or have
    pending sync updates are cached.

    Returns immediately if isCaching() is False.
    '''

    with self:
      if not self.isCaching():
        return

      data = {}

      with sgEntity:
        if not sgEntity.exists():
          return

        for name, field in sgEntity.fields().items():
          if not field.isCacheable():
            continue

          if field.hasSyncUpdate():
            data[name] = copy.deepcopy(field._updateValue)
          else:
            data[name] = field.toFieldData()

        #data['id'] = sgEntity['id']
        #data['type'] = sgEntity['type']

      cache = self.__entityCache[sgEntity.type][sgEntity['id']]

      cache['cache'] = data
      cache['entity'] = None

  def _createEntity(self, sgEntityType, sgData, sgSyncFields=None):
    '''
    Internal function!

    Locks the connection and if the Entity has an ID the cache is checked to see
    if it already has an SgEntity and if so it returns it otherwise it creates one.
    '''

    ShotgunORM.LoggerConnection.debug('%(connection)s._createEntity(...)', {'connection': self})
    ShotgunORM.LoggerConnection.debug('    * sgEntityType: %(entityName)s', {'entityName': sgEntityType})
    ShotgunORM.LoggerConnection.debug('    * sgData: %(sgData)s', {'sgData': sgData})

    with self:
      sgData = dict(sgData)

      factory = self.classFactory()

      result = None

      eId = None

      if sgData.has_key('id'):
        eId = int(sgData['id'])
      else:
        eId = -1

      if not self.__entityCache.has_key(sgEntityType):
        self.__entityCache[sgEntityType] = {}

      # Return immediately if the Entity does not exist.
      if eId <= -1:
        sgData['id'] = -id(result)

        result = factory.createEntity(self, sgEntityType, sgData)

        ShotgunORM.onEntityCreate(result)

        return result

      onCreate = False

      # Check the cache and if its found update any non-valid fields that
      # have data contained in the passed sgData.  If not found create the
      # Entity and add it to the cache.]
      if self.__entityCache[sgEntityType].has_key(eId):
        result = self.__entityCache[sgEntityType][eId]['entity']

        if result != None:
          result = result()

        if result == None:
          cacheData = self.__entityCache[sgEntityType][eId]['cache']

          tmpData = {
            'id': eId,
            'type': sgEntityType
          }

          tmpData.update(cacheData)

          result = factory.createEntity(self, sgEntityType, tmpData)

          self.__entityCache[sgEntityType][eId]['entity'] = weakref.ref(result)

          onCreate = True

        with result:
          del sgData['id']
          del sgData['type']

          for field, value in sgData.items():
            fieldObj = result.field(field)

            if fieldObj.isValid() or fieldObj.hasCommit() or fieldObj.hasSyncUpdate():
              continue

            fieldObj.invalidate()

            fieldObj._updateValue = value

            fieldObj.setHasSyncUpdate(True)
      else:
        result = factory.createEntity(self, sgEntityType, sgData)

        self.__entityCache[sgEntityType][eId] = {
          'entity': weakref.ref(result),
          'cache': {}
        }

        onCreate = True

      if sgSyncFields != None:
        result.sync(sgSyncFields, ignoreValid=True, ignoreWithUpdate=True, backgroundPull=True)

      if onCreate:
        ShotgunORM.onEntityCreate(result)

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

  def _batch(self, requests):
    def undoEntities(batchConfigs, exception):
      if len(batchConfigs) <= 0:
        return

      for data in batchConfigs:
        entity = data['entity']
        batchData = data['batch_data']
        commitData = data['commit_data']

        try:
          entity.afterCommit(batchData, None, commitData, exception)
        except:
          pass

    if len(requests) <= 0:
      return

    batchConfigs = []
    batchData = []
    batchSize = []

    for i in requests:
      entity = i['entity']

      entityBatchData = i['batch_data']

      commitData = {}

      try:
        entity.beforeCommit(entityBatchData, commitData)
      except Exception, e:
        try:
          entity.afterCommit(entityBatchData, None, commitData, e)
        except:
          pass

        undoEntities(batchConfigs, e)

        raise e

      batchConfigs.append(
        {
          'entity': entity,
          'batch_data': entityBatchData,
          'commit_data': commitData
        }
      )

      batchData.extend(entityBatchData)
      batchSize.append(len(entityBatchData))

    try:
      sgResult = self._sg_batch(batchData)
    except Exception, e:
      undoEntities(batchConfigs, e)

      raise e

    exception = None

    for configData in batchConfigs:
      entity = configData['entity']
      entityBatchData = configData['batch_data']
      entityCommitData = configData['commit_data']

      resultSize = batchSize.pop(0)

      entityResult = []

      for n in xrange(0, resultSize):
        entityResult.append(sgResult.pop(0))

      try:
        entity.afterCommit(entityBatchData, entityResult, entityCommitData, None)
      except Exception, e:
        if exception == None:
          exception = e

    if exception != None:
      raise exception

    return sgResult

  def batch(self, requests):
    '''
    Make a batch request of several create, update, and/or delete calls at one
    time. This is for performance when making large numbers of requests, as it
    cuts down on the overhead of roundtrips to the server and back. All requests
    are performed within a transaction, and if any request fails, all of them
    will be rolled back.
    '''

    if isinstance(requests, ShotgunORM.SgEntity):
      requests = [requests]

    if len(requests) <= 0:
      return []

    # Lock the Entities down.
    for entity in requests:
      entity._lock()

    batchRequests = []

    for entity in requests:
      try:
        commitData = entity.toBatchData()
      except Exception, e:
        for entity in requests:
          entity._unlock()

        raise e

      if len(commitData) <= 0:
        continue

      batchRequests.append(
        {
          'entity': entity,
          'batch_data': commitData
        }
      )

    self._batch(batchRequests)

  def classFactory(self):
    '''
    Returns the SgEntityClassFactory used by this connection to create Entity
    objects.
    '''

    return self._factory

  def clearCache(self, sgEntityTypes=None):
    '''
    Clears all cached Entities.

    Args:
      * (list) sgEntityTypes:
        List of Entity types to clear.
    '''

    with self:
      if sgEntityTypes == None:
        self.__entityCache = {}
      else:
        if isinstance(sgEntityTypes, str):
          sgEntityTypes = [sgEntityTypes]

        for i in sgEntityTypes:
          if self.__entityCache.has_key(i):
            del self.__entityCache[i]

  def create(self, sgEntityType, sgData={}, sgCommit=False, numberOfEntities=1):
    '''
    Creates a new Entity and returns it.  The returned Entity does not exist in
    the Shotgun database.

    Args:
      * (str) sgEntityType:
        Type of Entity to create.

      * (dict) sgData:
        Shotgun formated dictionary of field data.

      * (bool) sgCommit:
        Commits the result immediately to Shotgun.

      * (int) numberOfEntities:
        Number of Entities to create.
    '''

    ShotgunORM.LoggerConnection.debug('%(connection)s.create(...)', {'connection': self})
    ShotgunORM.LoggerConnection.debug('    * sgEntityType: %(entityName)s', {'entityName': sgEntityType})
    ShotgunORM.LoggerConnection.debug('    * sgData: %(sgData)s', {'sgData': sgData})
    ShotgunORM.LoggerConnection.debug('    * sgCommit: %(sgCommit)s', {'sgCommit': sgCommit})

    factory = self.classFactory()

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

    with sgEntity:
      batchData = [
        {
          'request_type': 'delete',
          'entity_type': sgEntity.type,
          'entity_id': sgEntity['id']
        }
      ]

      commitData = [
        {
          'entity': sgEntity,
          'batch_data': batchData
        }
      ]

      sgResult = self._batch(commitData)

      return sgResult[0]

  def defaultEntityQueryFields(self, sgEntityType):
    '''
    Returns the default query fields.

    Args:
      * (str) sgEntityType:
        Entity type.
    '''

    schema = self.schema()

    result = schema.defaultEntityQueryFields(
      self.fieldQueryTemplate(),
      schema.entityApiName(sgEntityType),
      self.fieldQueryTemplateFallback()
    )

    if result == set(['all']):
      result = set(schema.entityInfo(sgEntityType).fieldNames())
    elif result == set(['none']):
      result = set([])

    return result

  def disableCaching(self):
    '''
    Disables the caching of Entities.
    '''

    with self:
      if not self.isCaching():
        return False

      self.__entityCaching = False

      self.clearCache()

      return True

  def enableCaching(self):
    '''
    Enables the caching of Entities.
    '''

    with self:
      if self.isCaching():
        return False

      self.__entityCaching = True

      return True

  def fieldQueryTemplate(self):
    '''
    Returns the name of the template used for default field queries.
    '''

    return self._fieldQueryDefaults

  def fieldQueryTemplateFallback(self):
    '''
    Returns the name of the fallback template used for default field queries.
    '''

    return self._fieldQueryDefaultsFallback

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

    schema = self.schema()

    entity_type = schema.entityApiName(entity_type)
    filters = self._flattenFilters(filters)

    if fields == None:
      fields = self.defaultEntityQueryFields(entity_type)
    else:
      if isinstance(fields, str):
        fields = [fields]

      fields = set(fields)

      if 'default' in fields:
        fields.discard('default')

        fields.update(self.defaultEntityQueryFields(entity_type))

      if 'all' in fields:
        fields.discard('all')

        fields.update(schema.entityInfo(entity_type).fieldNames())

    ShotgunORM.LoggerConnection.debug('%(sgConnection)s.find(...)', {'sgConnection': self})
    ShotgunORM.LoggerConnection.debug('    * entity_type: %(entityType)s', {'entityType': entity_type})
    ShotgunORM.LoggerConnection.debug('    * filters: %(sgFilters)s', {'sgFilters': filters})
    ShotgunORM.LoggerConnection.debug('    * fields: %(sgFields)s', {'sgFields': fields})

    searchResult = self._sg_find(
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

      * (bool) retired_only:
        Return only retired entities.
    '''

    if isinstance(filters, int):
      schema = self.schema()

      entity_type = schema.entityApiName(entity_type)

      if self.__entityCache.has_key(entity_type):
        iD = filters

        if self.__entityCache[entity_type].has_key(iD):
          return self._createEntity(entity_type, {'id': iD, 'type': entity_type}, fields)

    searchResult = self.find(
      entity_type=entity_type,
      filters=filters,
      fields=fields,
      order=order,
      filter_operator=filter_operator,
      limit=1,
      retired_only=retired_only
    )

    if len(searchResult) >= 1:
      return searchResult[0]
    else:
      return None

  def isCaching(self):
    '''
    Returns True if the connection is caching Entities
    '''

    return self.__entityCaching

  def queryEngine(self):
    '''
    Query Engine that performs background Entity field pulling.
    '''

    return self.__qEngine

  def revive(self, sgEntity):
    '''
    Revives (un-deletes) the Entity matching entity_type and entity_id.

    Args:
      * (SgEntity) sgEntity
        Entity to revive
    '''

    with sgEntity:
      batchData = [
        {
          'request_type': 'revive',
          'entity_type': sgEntity.type,
          'entity_id': sgEntity['id']
        }
      ]

      commitData = {}

      try:
        sgEntity.beforeCommit(batchData, commitData)
      except Exception, e:
        try:
          sgEntity.afterCommit(batchData, None, commitData, e)
        except:
          pass

        raise e

      sgResult = None

      try:
        sgResult = self._sg_revive(sgEntity.type, sgEntity['id'])
      except Exception, e:
        try:
          sgEntity.afterCommit(batchData, None, commitData, e)
        except:
          pass

        raise e

      sgEntity.afterCommit(batchData, [sgResult], commitData)

      return sgResult

  def schema(self):
    '''
    Returns the SgSchema used by the connection.
    '''

    return self.__schema

  def schemaChanged(self):
    '''
    This is called when the parent SgConnection's schema has been updated.
    '''

    factory = self.classFactory()

    with self:
      factory.build()

      # Blast the field cache.
      self.clearCache()

    # In the future this could support live updating of SgEntityInfo objects.

  def search(self, sgEntityType, sgSearchExp, sgFields=None, sgSearchArgs=[], order=None, limit=0, retired_only=False, page=0):
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
        result set.
    '''

    schema = self.schema()

    sgconnection = self.connection()

    entity_type = schema.entityApiName(sgEntityType)

    ShotgunORM.LoggerConnection.debug('%(sgConnection)s.search(...)', {'sgConnection': self})
    ShotgunORM.LoggerConnection.debug('    * entity_type: %(entityType)s', {'entityType': entity_type})
    ShotgunORM.LoggerConnection.debug('    * search_exp: "%(sgSearchExp)s"', {'sgSearchExp': sgSearchExp})
    ShotgunORM.LoggerConnection.debug('    * fields: %(sgFields)s', {'sgFields': sgFields})

    filters = ShotgunORM.parseToLogicalOp(
      schema.entityInfo(entity_type),
      sgSearchExp,
      sgSearchArgs
    )

    filters = self._flattenFilters(filters)

    if sgFields == None:
      sgFields = self.defaultEntityQueryFields(entity_type)
    else:
      if isinstance(sgFields, str):
        sgFields = [sgFields]

      sgFields = set(sgFields)

      if 'default' in sgFields:
        sgFields.discard('default')

        sgFields.update(self.defaultEntityQueryFields(entity_type))

    return self.find(
      entity_type,
      filters,
      sgFields,
      order=order,
      limit=limit,
      retired_only=retired_only,
      page=page
    )

  def searchOne(self, sgEntityType, sgSearchExp, sgFields=None, sgSearchArgs=[], order=None, retired_only=False):
    '''
    Same as search(...) but only returns a single Entity.

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
    '''

    result = self.search(sgEntityType, sgSearchExp, sgFields, sgSearchArgs, order=order, limit=1, retired_only=retired_only)

    if len(result) >= 1:
      return result[0]

    return None

  def setFieldQueryTemplate(self, sgQueryTemplate):
    '''
    Sets the connections default field query template.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    if not isinstance(sgQueryTemplate, (str, types.NoneType)):
      raise TypeError('expected a str for sgQueryTemplate, got %s' % type(sgQueryTemplate).__name__)

    self._fieldQueryDefaults = sgQueryTemplate

  def setFieldQueryTemplateFallback(self, sgQueryTemplate):
    '''
    Sets the connections default field query template fallback.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    if not isinstance(sgQueryTemplate, (str, types.NoneType)):
      raise TypeError('expected a str for sgQueryTemplate, got %s' % type(sgQueryTemplate).__name__)

    self._fieldQueryDefaultsFallback = sgQueryTemplate
