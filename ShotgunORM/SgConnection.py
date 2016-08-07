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
  'SgConnection',
  'SgConnectionMeta'
]

# Python imports
import atexit
import copy
import os
import re
import threading
import types
import weakref
import webbrowser

# This module imports
import ShotgunORM

SHUTTING_DOWN = False

def sgorm_connection_atexit():
  global SHUTTING_DOWN

  SHUTTING_DOWN = True

atexit.register(sgorm_connection_atexit)

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

      classConnections = result.__connections__

      scriptName = result._scriptName
      scriptKey = result._scriptKey

      try:
        ref = classConnections[urlLower][scriptName][scriptKey]

        refResult = ref()

        if refResult != None:
          return refResult
      except KeyError:
        pass

      resultWeak = weakref.ref(result)

      if not classConnections.has_key(urlLower):
        classConnections[urlLower] = {
          scriptName: {
            scriptKey: resultWeak
          }
        }
      elif not classConnections[urlLower].has_key(scriptName):
        classConnections[urlLower][scriptName] = {
          scriptKey: resultWeak
        }
      else:
        classConnections[urlLower][scriptName][scriptKey] = resultWeak

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
      result.asyncEngine().start()

      return result

  @classmethod
  def connections(cls, url):
    '''
    Returns all the active SgConnection objects for a given URL string.
    '''

    url = url.lower()

    connections = []

    for weakConnection in cls.__connections__.get(url.lower(), {}).values():
        connection = weakConnection

        if connection:
          connections.append(connection)

    return connections

class SgConnectionPriv(object):
  '''
  Private base class for Shotgun connections.

  This class is a wrapper to the Shotgun Python API.
  '''

  __metaclass__ = SgConnectionMeta

  def __init__(
    self,
    url,
    scriptName,
    scriptkey,
    datetimeToUtc=True,
    httpProxy=None,
    ensureASCII=True,
    connect=False,
    caCerts=None,
    login=None,
    password=None,
    suAsLogin=None,
    sessionToken=None,
    authToken=None
  ):
    self._url = str(url)
    self._scriptName = str(scriptName)
    self._scriptKey = str(scriptkey)

    self._connection = ShotgunORM.SHOTGUN_API.shotgun.Shotgun(
       base_url=self._url,
       script_name=self._scriptName,
       api_key=self._scriptKey,
       convert_datetimes_to_utc=datetimeToUtc,
       http_proxy=httpProxy,
       ensure_ascii=ensureASCII,
       connect=connect,
       ca_certs=caCerts,
       login=login,
       password=password,
       sudo_as_login=suAsLogin,
       session_token=sessionToken,
       auth_token=authToken
    )

    self._facility = None

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
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Calls the Shotgun Python API find function.

    This will lock the global Shotgun Python API lock.
    '''

    if fields != None:
      fields = list(fields)

    with ShotgunORM.SHOTGUN_API_LOCK:
      result = self.connection().find(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        limit,
        retired_only,
        page,
        include_archived_projects,
        additional_filter_presets
      )

      return ShotgunORM.onSearchResult(
        self,
        entity_type,
        fields,
        result
      )

  def _sg_find_one(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Calls the Shotgun Python API find_one function.

    This will lock the global Shotgun Python API lock.
    '''

    if fields != None:
      fields = list(fields)

    with ShotgunORM.SHOTGUN_API_LOCK:
      result = self.connection().find_one(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        retired_only,
        include_archived_projects,
        additional_filter_presets
      )

      return ShotgunORM.onSearchResult(
        self,
        entity_type,
        fields,
        [result]
      )[0]

  def _sg_revive(self, entityType, entityId):
    '''
    Calls the Shotgun Python API revive function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().revive(entityType, entityId)

  def _sg_schema_entity_read(self, project_entity=None):
    '''

    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().schema_entity_read(project_entity)

  def _sg_schema_field_read(self, entity_type, field_name=None, project_entity=None):
    '''

    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().schema_field_read(entity_type, field_name, project_entity)

  def _sg_schema_read(self, project_entity=None):
    '''

    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().schema_read(project_entity)

  def _sg_summarize(
    self,
    entity_type,
    filters,
    summary_fields,
    filter_operator=None,
    grouping=None,
    include_archived_projects=True
  ):
    '''
    Calls the Shotgun Python API summarize function.

    This will lock the global Shotgun Python API lock.
    '''

    with ShotgunORM.SHOTGUN_API_LOCK:
      return self.connection().summarize(
        entity_type,
        filters,
        summary_fields,
        filter_operator,
        grouping,
        include_archived_projects
      )

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

  def facility(self):
    '''
    Returns the facility name from the Shotgun url.
    '''

    if self._facility == None:
      self._facility = ShotgunORM.facilityNameFromUrl(self._url)

    return self._facility

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

  def scriptName(self):
    '''
    Returns the Shotgun script name for the connection.
    '''

    return self._scriptName

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
    return '<%s(url:"%s", script:"%s")>' % (
      self.__class__.__name__,
      self.url(),
      self.scriptName()
    )

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

  def __init__(
    self,
    url,
    scriptName,
    scriptKey,
    datetimeToUtc=True,
    httpProxy=None,
    ensureASCII=True,
    connect=False,
    caCerts=None,
    login=None,
    password=None,
    suAsLogin=None,
    sessionToken=None,
    authToken=None,
    baseEntityClasses={},
    enableUndo=False
  ):
    super(SgConnection, self).__init__(
      url,
      scriptName,
      scriptKey,
      datetimeToUtc=datetimeToUtc,
      httpProxy=httpProxy,
      ensureASCII=ensureASCII,
      connect=connect,
      caCerts=caCerts,
      login=login,
      password=password,
      suAsLogin=suAsLogin,
      sessionToken=sessionToken,
      authToken=authToken
    )

    self.__lockCache = threading.RLock()

    self._fieldQueryDefaults = 'default'
    self._fieldQueryDefaultsFallback = 'default'

    baseClasses = self.baseEntityClasses()

    if baseClasses == None:
      baseClasses = {}

    if baseEntityClasses == None:
      baseEntityClasses = {}

    baseClasses.update(baseEntityClasses)

    self.__qEngine = ShotgunORM.SgQueryEngine(self)
    self.__asyncEngine = ShotgunORM.SgAsyncSearchEngine(self)
    self.__schema = ShotgunORM.SgSchema.createSchema(self._url)
    self._factory = ShotgunORM.SgEntityClassFactory(
      self,
      baseClasses
    )

    if enableUndo == True:
      self.__undo = ShotgunORM.SgUndo(self)
    else:
      self.__undo = ShotgunORM.SgUndo(self, ShotgunORM.SgUndoStackRoot())

    self.__entityCache = {}
    self.__entityCaching = ShotgunORM.config.DEFAULT_CONNECTION_CACHING

    self.__currentUser = None

  @classmethod
  def siteConnections(cls, url):
    '''
    Returns all the active SgConnection objects for a given URL string.
    '''

    return cls.__metaclass__.connections(url)

  def _addEntity(self, sgEntity):
    '''
    Internal function!

    Used by SgEntities and SgConnections when they commit a new Entity to
    Shotgun.
    '''

    with self:
      self.__entityCache[sgEntity.type][sgEntity['id']] = {
        'entity': weakref.ref(sgEntity),
        'cache': {}
      }

  def _createEntity(self, sgEntityType, sgData, sgSyncFields=None):
    '''
    Internal function!

    Locks the connection and if the Entity has an ID the cache is checked to see
    if it already has an SgEntity and if so it returns it otherwise it creates
    one.
    '''

    ShotgunORM.LoggerConnection.debug(
      '%(connection)s._createEntity(...)', {'connection': self}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * sgEntityType: %(entityName)s', {'entityName': sgEntityType}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * sgData: %(sgData)s', {'sgData': sgData}
    )

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
        result = factory.createEntity(sgEntityType, sgData)

        ShotgunORM.onEntityCreate(result)

        return result

      onCreate = False

      # Check the cache and if its found update any non-valid fields that
      # have data contained in the passed sgData.  If not found create the
      # Entity and add it to the cache.]
      if self.__entityCache[sgEntityType].has_key(eId):
        cacheData = self.__entityCache[sgEntityType][eId]
        result = cacheData['entity']

        if result != None:
          result = result()

        if result == None:
          tmpData = {
            'id': eId,
            'type': sgEntityType
          }

          tmpData.update(cacheData['cache'])

          result = factory.createEntity(sgEntityType, tmpData)

          result._SgEntity__caching = cacheData['cache_state']

          cacheData['entity'] = weakref.ref(result)

          onCreate = True

        with result:
          del sgData['id']
          del sgData['type']

          for field, value in sgData.items():
            fieldObj = result.field(field)

            if (
              fieldObj == None or
              fieldObj.isValid() or
              fieldObj.hasCommit() or
              fieldObj.hasSyncUpdate()
            ):
              continue

            fieldObj.invalidate()

            fieldObj._updateValue = value

            fieldObj.setHasSyncUpdate(True)
      else:
        result = factory.createEntity(sgEntityType, sgData)

        self.__entityCache[sgEntityType][eId] = {
          'entity': weakref.ref(result),
          'cache': {},
          'cache_state': -1
        }

        onCreate = True

      if sgSyncFields != None:
        result.sync(
          sgSyncFields,
          ignoreValid=True,
          ignoreWithUpdate=True,
          backgroundPull=True
        )

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

  def _batch(self, requests, sgDryRun):
    def undoEntities(batchConfigs, exception):
      if len(batchConfigs) <= 0:
        return

      for data in batchConfigs:
        entity = data['entity']
        batchData = data['batch_data']
        commitData = data['commit_data']

        try:
          entity.afterCommit(batchData, None, commitData, sgDryRun, exception)
        except:
          pass

    if len(requests) <= 0:
      return []

    batchConfigs = []
    batchData = []
    batchSize = []

    for i in requests:
      entity = i['entity']

      entityBatchData = i['batch_data']

      commitData = {}

      try:
        entity.beforeCommit(entityBatchData, commitData, sgDryRun)
      except Exception, e:
        try:
          entity.afterCommit(entityBatchData, None, commitData, sgDryRun, e)
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

    undo_stack = self.undo()

    undo_action = None

    try:
      if sgDryRun == True:
        sgResult = []

        for batchJob in batchData:
          jobType = batchJob['request_type']

          if jobType == 'update':
            data = {
              'type': batchJob['entity_type'],
              'id': batchJob['entity_id'],
            }

            data.update(batchJob['data'])

            sgResult.append(data)
          elif jobType == 'create':
            data = {
              'type': batchJob['entity_type'],
            }

            data.update(batchJob['data'])

            data['id'] = -1

            sgResult.append(data)
          elif jobType in ['delete', 'revive']:
            sgResult.append(True)
      else:
        sgResult = self._sg_batch(batchData)

        undo_action = ShotgunORM.SgUndoAction(batchData, sgResult)

      result = copy.deepcopy(sgResult)
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
        entity.afterCommit(
          entityBatchData,
          entityResult,
          entityCommitData,
          sgDryRun,
          None
        )
      except Exception, e:
        if exception == None:
          exception = e

    if exception != None:
      raise exception

    return result

  def addAsyncSearch(self, sgAsyncSearchResult):
    '''
    Add the SgAsyncSearchResult to the front of the async search queue.
    '''

    self.__asyncEngine.addToQueue(sgAsyncSearchResult)

  def appendAsyncSearch(self, sgAsyncSearchResult):
    '''
    Add the SgAsyncSearchResult to the back of the async search queue.
    '''

    self.__asyncEngine.appendToQueue(sgAsyncSearchResult)

  def asyncEngine(self):
    '''
    Async search engine that performs background searches.
    '''

    return self.__asyncEngine

  def baseEntityClasses(self):
    '''
    Returns a dict that will be passed to the connections class factory during
    initialization.

    The dictionary keys should be Entity names and the value a pointer to the
    class which will be used as the base class for that particular Entity
    type.

    Subclasses can implement this function to allow a connection to specifiy
    custom Entity classes without overriding the global base Entity class.
    '''

    return {}

  def batch(self, requests, sgDryRun=False):
    '''
    Make a batch request of several create, update, and/or delete calls at one
    time. This is for performance when making large numbers of requests, as it
    cuts down on the overhead of roundtrips to the server and back. All requests
    are performed within a transaction, and if any request fails, all of them
    will be rolled back.
    '''

    if isinstance(requests, ShotgunORM.SgEntity):
      requests = set([requests])

    if len(requests) <= 0:
      return []

    requests = set(requests)

    # Lock the Entities down.
    for entity in requests:
      entity._lock()

    batchRequests = []

    try:
      for entity in requests:
        if entity.connection() != self:
          raise ValueError(
            'entity %s does not belong to this connection %s' % (entity, self)
          )

        commitData = entity.toBatchData()

        if len(commitData) <= 0:
          continue

        batchRequests.append(
          {
            'entity': entity,
            'batch_data': commitData
          }
        )

      result = self._batch(batchRequests, sgDryRun)

      return result
    finally:
      for entity in requests:
        entity._unlock()

  def cacheEntity(self, sgEntity):
    '''
    Caches the passed Entities field values.

    Only fields that contain no commit update and are either valid or have
    pending sync updates are cached.

    Returns immediately if sgEntity.isCaching() is False.

    Args:
      * (SgEntity) sgEntity:
        Entity that will have its data cache.
    '''

    global SHUTTING_DOWN

    if SHUTTING_DOWN == True:
      return

    with sgEntity:
      if not sgEntity.exists() or not sgEntity.isCaching():
        return

      with self:
        # Bail if the cache has been cleared.  The Entity is dirty!
        if (
          not self.__entityCache.has_key(sgEntity.type) or
          not self.__entityCache[sgEntity.type].has_key(sgEntity['id'])
        ):
          return

        cache = self.__entityCache[sgEntity.type][sgEntity['id']]

        e = cache['entity']()

        # If the cache was cleared and a new Entity object created this one is
        # dirty and don't allow it to store cache data.
        if e != None:
          if id(e) != id(sgEntity):
            return

        data = {}

        with sgEntity:
          for name, field in sgEntity.fields().items():
            if not field.isCacheable():
              continue

            data[name] = field.toFieldData()

          #data['id'] = sgEntity['id']
          #data['type'] = sgEntity['type']

        if len(data) == 0:
          del self.__entityCache[sgEntity.type][sgEntity['id']]

          return

        cache['cache'] = data
        cache['cache_state'] = sgEntity.caching()

  def classFactory(self):
    '''
    Returns the SgEntityClassFactory used by this connection to create Entity
    objects.
    '''

    return self._factory

  def clearCache(self, sgEntityTypes=None, fieldValuesOnly=True):
    '''
    Clears all cached Entities.

    Args:
      * (list) sgEntityTypes:
        List of Entity types to clear.

      * (bool) fieldValuesOnly:
        Only clear field values for Entities that are not currently in scope.
        This will leave any weakref links to alive Entity objects alone.  Any
        such Entity will have the ability to cache field values when gc'd.
    '''

    with self:
      if fieldValuesOnly:
        if sgEntityTypes == None:
          for entityType, entityCaches in self.__entityCache.items():
            for entityId, entityCache in entityCaches.items():
              entityCache['cache'].clear()
        else:
          if isinstance(sgEntityTypes, str):
            sgEntityTypes = [sgEntityTypes]

          for i in sgEntityTypes:
            if not self.__entityCache.has_key(i):
              continue

            for entityId, entityCache in self.__entityCache[i].items():
              entityCache['cache'].clear()
      else:
        if sgEntityTypes == None:
          self.__entityCache = {}
        else:
          if isinstance(sgEntityTypes, str):
            sgEntityTypes = [sgEntityTypes]

          for i in sgEntityTypes:
            try:
              del self.__entityCache[i]
            except KeyError:
              pass

  def clearCacheForEntity(self, sgEntity, fieldValuesOnly=True):
    '''
    Removes any cached data for a specific Entity.

    Args:
      * (SgEntity) sgEntity:
        Entity that will have its cache data purged.

      * (bool) fieldValuesOnly:
        Only clear field values for the Entity that are not currently in scope.
        This will leave any weakref links to the Entity object alone.
    '''

    with sgEntity:
      if not sgEntity.exists():
        return

      with self:
        entityTypeCacheData = self.__entityCache.get(sgEntity.type, {})

        try:
          entityTypeCacheData[sgEntity.id]['cache_state'] = sgEntity.caching()

          if fieldValuesOnly:
            entityTypeCacheData[sgEntity.id]['cache'].clear()
          else:
            del entityTypeCacheData[sgEntity.id]
        except KeyError:
          pass

  def currentUser(self, sgFields=None):
    '''
    Searches Shotgun for a HumanUser with a login of the current system user
    and returns the Entity if found.

    Args:
      * (list) sgFields:
        Fields that Entity will have filled in with data from Shotgun.
    '''

    if self.__currentUser == None:
      username = os.getenv('USER', None)

      if username == None:
        username = os.getenv('USERNAME')

        if username == None:
          self.__currentUser = -1

          return None

      user = self.findOne(
        'HumanUser',
        [['login', 'is', username]]
      )

      if user == None:
        return None

      self.__currentUser = user['id']

      return user

    elif self.__currentUser == -1:
      return None
    else:
      return self._createEntity(
        'HumanUser',
        {
          'id': self.__currentUser,
          'type': 'HumanUser'
        },
        sgFields
      )

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

    ShotgunORM.LoggerConnection.debug(
      '%(connection)s.create(...)', {'connection': self}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * sgEntityType: %(entityName)s', {'entityName': sgEntityType}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * sgData: %(sgData)s', {'sgData': sgData}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * sgCommit: %(sgCommit)s', {'sgCommit': sgCommit}
    )

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

  def delete(self, sgEntity, sgDryRun=False):
    '''
    Deletes the passed Entity from Shotgun.

    Args:
      * (SgEntity) sgEntity:
        Entity to delete.
    '''

    with sgEntity:
      if sgEntity.connection() != self:
        raise ValueError(
          'entity %s does not belong to this connection %s' % (sgEntity, self)
        )

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

      sgResult = self._batch(commitData, sgDryRun)

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

      # No need to break links for currently alive Entity objects so just clear
      # the field value cache.
      self.clearCache(fieldValuesOnly=True)

      return True

  def enableCaching(self):
    '''
    Enables the caching of Entities.
    '''

    with self:
      self.__entityCaching = True

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
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None
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
        options: all and any. You cannot currently combine the two options in
        the same query.

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

    ShotgunORM.LoggerConnection.debug(
      '%(sgConnection)s.find(...)', {'sgConnection': self}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * entity_type: %(entityType)s', {'entityType': entity_type}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * filters: %(sgFilters)s', {'sgFilters': filters}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * fields: %(sgFields)s', {'sgFields': fields}
    )

    searchResult = self._sg_find(
      entity_type=entity_type,
      filters=filters,
      fields=fields,
      order=order,
      filter_operator=filter_operator,
      limit=limit,
      retired_only=retired_only,
      page=page,
      include_archived_projects=include_archived_projects,
      additional_filter_presets=additional_filter_presets
    )

    if searchResult != None:
      newResult = []

      for i in searchResult:
        newResult.append(self._createEntity(entity_type, i))

      searchResult = newResult

    return searchResult

  def findAsync(
    self,
    entity_type,
    filters,
    fields=None,
    order=None,
    filter_operator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Performs an async find() search.

    See find() for a more detailed description.
    '''

    return self.__asyncEngine.appendSearchToQueue(
      entity_type,
      filters,
      fields,
      order,
      filter_operator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

  def findIterator(
    self,
    entity_type,
    filters,
    fields=None,
    order=None,
    filter_operator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None,
    buffered=False
  ):
    '''
    Returns a SgSearchIterator which is used to iterate over the search filter
    by page.
    '''

    iterClass = None

    if buffered:
      iterClass = ShotgunORM.SgBufferedSearchIterator
    else:
      iterClass = ShotgunORM.SgSearchIterator

    return iterClass(
      self,
      entity_type,
      filters,
      fields,
      order,
      filter_operator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

  def findOne(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
    include_archived_projects=True,
    additional_filter_presets=None
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
        options: all and any. You cannot currently combine the two options in
        the same query.

      * (bool) retired_only:
        Return only retired entities.
    '''

    if isinstance(filters, int):
      schema = self.schema()

      entity_type = schema.entityApiName(entity_type)

      return self._createEntity(
        entity_type,
        {'id': filters, 'type': entity_type},
        fields
      )

    searchResult = self.find(
      entity_type=entity_type,
      filters=filters,
      fields=fields,
      order=order,
      filter_operator=filter_operator,
      limit=1,
      retired_only=retired_only,
      include_archived_projects=include_archived_projects,
      additional_filter_presets=additional_filter_presets
    )

    if len(searchResult) >= 1:
      return searchResult[0]
    else:
      return None

  def findOneAsync(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    retired_only=False,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Performs an async findOne() search.

    See findOne() for a more detailed description.
    '''

    return self.__asyncEngine.appendSearchToQueue(
      entity_type,
      filters,
      fields,
      order,
      filter_operator,
      0,
      retired_only,
      0,
      include_archived_projects,
      additional_filter_presets,
      isSingle=True
    )

  def info(self):
    '''
    Returns the Shotgun server api info.
    '''

    return ShotgunORM.SgServerInfo(self)

  def isCaching(self):
    '''
    Returns True if the connection is caching Entities
    '''

    return self.__entityCaching

  def isEntityVisibleToProject(self, sgEntity, sgProject):
    '''
    Returns True if the Shotgun Entity is visible.
    '''

    return True

  def isFieldVisibleToProject(self, sgProject, sgEntity, sgField):
    '''
    Returns True if the Shotgun Entity field is visible for the
    specified project.

    Args:
      * (SgEntity/str) sgProject:
        Name of the project.

      * (str) sgEntity:
        Name of the Entity.

      * (str) sgField:
        Name of the field.
    '''

    schema = self.schema()

    eInfo = None

    eInfo = schema.entityInfo(sgEntity)

    if eInfo == None:
      return False

    fInfo = eInfo.fieldInfo(sgField)

    if fInfo == None:
      return False

    if not isinstance(sgProject, ShotgunORM.SgEntity):
      sgProject = self.searchOne('Project', 'name == "%s"' % sgProject)

    sgProject = sgProject.toEntityFieldData()

    data = self._sg_schema_field_read(sgEntity, sgField, sgProject)

    try:
      return data['project']['visible']['value']
    except KeyError:
      return False
    except:
      raise

  def isValid(self):
    '''

    '''

    return self.schema().isInitialized()

  def project(self, sgProject, sgFields=None):
    '''
    Returns the project Entity named "sgProject".

    Args:
      * (str) sgProject:
        Name of the project.

      * (list) sgFields:
        List of fields to populate the result with.
    '''

    return self.findOne(
      'Project',
      [
        [
          'code',
          'is',
          sgProject
        ]
      ],
      sgFields
    )

  def projects(self, sgFields=None, sgProjectTypes=None, sgStatus=['Active']):
    '''
    Returns a list of project Entity objects.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (list) sgProjectTypes:
        List of project type names to filter the results by.

      * (list) sgStatus:
        List of project status values to filter the results by.
    '''

    filters = []

    if sgStatus != None and sgStatus != []:
      filters.append(
        [
          'sg_status',
          'in',
          list(sgStatus)
        ]
      )

    if sgProjectTypes != None and sgProjectTypes != []:
      filters.append(
        [
          'sg_type',
          'in',
          list(sgProjectTypes)
        ]
      )

    return self.find(
      'Project',
      filters,
      sgFields,
      order=[{'direction': 'asc', 'field_name': 'name'}]
    )

  def queryEngine(self):
    '''
    Query Engine that performs background Entity field pulling.
    '''

    return self.__qEngine

  def revive(self, sgEntity, sgDryRun=False):
    '''
    Revives (un-deletes) the Entity matching entity_type and entity_id.

    Args:
      * (SgEntity) sgEntity
        Entity to revive
    '''

    with sgEntity:
      if sgEntity.connection() != self:
        raise ValueError(
          'entity %s does not belong to this connection %s' % (sgEntity, self)
        )

      batchData = [
        {
          'request_type': 'revive',
          'entity_type': sgEntity.type,
          'entity_id': sgEntity['id']
        }
      ]

      commitData = {}

      try:
        sgEntity.beforeCommit(batchData, commitData, sgDryRun)
      except Exception, e:
        try:
          sgEntity.afterCommit(batchData, None, commitData, sgDryRun, e)
        except:
          pass

        raise e

      sgResult = None

      try:
        if sgDryRun:
          sgResult = True
        else:
          sgResult = self._sg_revive(sgEntity.type, sgEntity['id'])

          undo = self.undo()

          undo.push(ShotgunORM.SgUndoAction(batchData, [sgResult]))
      except Exception, e:
        try:
          sgEntity.afterCommit(batchData, None, commitData, sgDryRun, e)
        except:
          pass

        raise e

      sgEntity.afterCommit(batchData, [sgResult], commitData, sgDryRun)

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

    # In the future this could support live updating of SgEntitySchemaInfo objects.

  def search(
    self,
    sgEntityType,
    sgSearchExp,
    sgFields=None,
    sgSearchArgs=[],
    order=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
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

    ShotgunORM.LoggerConnection.debug(
      '%(sgConnection)s.search(...)', {'sgConnection': self}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * entity_type: %(entityType)s', {'entityType': entity_type}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * search_exp: "%(sgSearchExp)s"', {'sgSearchExp': sgSearchExp}
    )

    ShotgunORM.LoggerConnection.debug(
      '    * fields: %(sgFields)s', {'sgFields': sgFields}
    )

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
      page=page,
      include_archived_projects=include_archived_projects,
      additional_filter_presets=additional_filter_presets
    )

  def searchAsync(
    self,
    sgEntityType,
    sgSearchExp,
    sgFields=None,
    sgSearchArgs=[],
    order=None,
    filter_operator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Performs an async search().

    See search() for a more detailed description.
    '''

    schema = self.schema()

    sgEntityType = schema.entityApiName(sgEntityType)

    sgFilters = ShotgunORM.parseToLogicalOp(
      schema.entityInfo(sgEntityType),
      sgSearchExp,
      sgSearchArgs
    )

    sgFilters = self._flattenFilters(sgFilters)

    return self.__asyncEngine.appendSearchToQueue(
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filter_operator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

  def searchIterator(
    self,
    sgEntityType,
    sgSearchExp,
    sgFields=None,
    sgSearchArgs=[],
    order=None,
    filter_operator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None,
    buffered=False
  ):
    '''
    Returns a SgSearchIterator which is used to iterate over the search filter
    by page.
    '''

    schema = self.schema()

    sgEntityType = schema.entityApiName(sgEntityType)

    sgFilters = ShotgunORM.parseToLogicalOp(
      schema.entityInfo(sgEntityType),
      sgSearchExp,
      sgSearchArgs
    )

    sgFilters = self._flattenFilters(sgFilters)

    iterClass = None

    if buffered:
      iterClass = ShotgunORM.SgBufferedSearchIterator
    else:
      iterClass = ShotgunORM.SgSearchIterator

    return iterClass(
      self,
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filter_operator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

  def searchOne(
    self,
    sgEntityType,
    sgSearchExp,
    sgFields=None,
    sgSearchArgs=[],
    order=None,
    retired_only=False,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
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

    result = self.search(
      sgEntityType,
      sgSearchExp,
      sgFields,
      sgSearchArgs,
      order=order,
      limit=1,
      retired_only=retired_only,
      include_archived_projects=include_archived_projects,
      additional_filter_presets=additional_filter_presets
    )

    if len(result) >= 1:
      return result[0]

    return None

  def searchOneAsync(
    self,
    sgEntityType,
    sgSearchExp,
    sgFields=None,
    sgSearchArgs=[],
    order=None,
    filter_operator=None,
    retired_only=False,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Performs an async searchOne().

    See searchOne() for a more detailed description.
    '''

    schema = self.schema()

    sgEntityType = schema.entityApiName(sgEntityType)

    sgFilters = ShotgunORM.parseToLogicalOp(
      schema.entityInfo(sgEntityType),
      sgSearchExp,
      sgSearchArgs
    )

    sgFilters = self._flattenFilters(sgFilters)

    return self.__asyncEngine.appendSearchToQueue(
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filter_operator,
      0,
      retired_only,
      0,
      isSingle=True
    )

  def setFieldQueryTemplate(self, sgQueryTemplate):
    '''
    Sets the connections default field query template.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    if not isinstance(sgQueryTemplate, (str, types.NoneType)):
      raise TypeError(
        'expected a str for sgQueryTemplate, got %s' %
        type(sgQueryTemplate).__name__
      )

    self._fieldQueryDefaults = sgQueryTemplate

  def setFieldQueryTemplateFallback(self, sgQueryTemplate):
    '''
    Sets the connections default field query template fallback.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    if not isinstance(sgQueryTemplate, (str, types.NoneType)):
      raise TypeError(
        'expected a str for sgQueryTemplate, got %s' %
        type(sgQueryTemplate).__name__
      )

    self._fieldQueryDefaultsFallback = sgQueryTemplate

  def setTimeout(self, secs):
    '''
    Set the timeout value which searchs will fail after N seconds have ellapsed.

    Args:
      * (None or int) secs:
        Number of seconds.
    '''

    if secs != None:
      secs = int(secs)

    self.connection().config.timeout_secs = secs

  def summarize(
    self,
    entity_type,
    filters,
    summary_fields,
    filter_operator=None,
    grouping=None,
    include_archived_projects=True
  ):
    '''

    '''

    return self._sg_summarize(
      entity_type,
      filters,
      summary_fields,
      filter_operator,
      grouping,
      include_archived_projects
    )

  def timeout(self):
    '''
    Returns the number of seconds that searches will fail after N seconds have
    ellapsed.
    '''

    return self.connection().config.timeout_secs

  def undo(self):
    '''

    '''

    return self.__undo

  def user(self, sgUser, sgFields=None):
    '''
    Returns the HumanUser Entity belonging to the user "sgUser".

    Args:
      * (str) sgUser:
        Name of the Shotgun user.

      * (list) sgFields:
        List of fields to populate the result with.
    '''

    return self.findOne(
      'HumanUser',
      [
        [
          'name',
          'is',
          sgUser
        ]
      ],
      sgFields
    )

  def users(self, sgFields=None, sgActiveOnly=True, sortByLastName=False):
    '''
    Returns a list of HumanUser Entities
    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (bool) sgActiveOnly:
        Return only active users when True.
    '''

    # Filter bogus users
    filters = [
      [
        'name',
        'is_not',
        'Shotgun Support'
      ],
      [
        'name',
        'not_contains',
        'Template User'
      ]
    ]

    if sgActiveOnly:
      filters.append(
        [
          'sg_status_list',
          'is',
          'act'
        ]
      )

    direction = 'asc'

    if sortByLastName:
      direction = 'desc'

    return self.find(
      'HumanUser',
      filters,
      sgFields,
      order=[{'direction': direction, 'field_name': 'name'}]
    )
