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
  'SgSchema'
]

# Python imports
import datetime
import hashlib
import os
import threading
import time
import weakref

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

def _entityFix(schema, schemaData):
  '''
  Returns Entities that dont exist in the API but fields return them as values.

  * Currently returns *

    1: Banner Entity
    2: AppWelcome Entity
  '''

  idInfoData = ShotgunORM.SgFieldSchemaInfo.createSchemaData(
    'Banner',
    'id',
    ShotgunORM.SgField.RETURN_TYPE_INT,
    editable=False,
    doc='Entity ID',
    label='Id'
  )

  nameInfoData = ShotgunORM.SgFieldSchemaInfo.createSchemaData(
    'Banner',
    'name',
    ShotgunORM.SgField.RETURN_TYPE_TEXT,
    editable=False,
    label='Name'
  )

  bannerFieldInfos = {
    'name': ShotgunORM.SgFieldSchemaInfo(nameInfoData),
    'id': ShotgunORM.SgFieldSchemaInfo(idInfoData)
  }

  BannerEntity = ShotgunORM.SgEntitySchemaInfo(
    schema,
    'Banner',
    'Banner',
    bannerFieldInfos,
    {}
  )

  ShotgunORM.onEntitySchemaInfoCreate(BannerEntity)

  idInfoData = ShotgunORM.SgFieldSchemaInfo.createSchemaData(
    'AppWelcome',
    'id',
    ShotgunORM.SgField.RETURN_TYPE_INT,
    doc='Entity ID',
    editable=False,
    label='Id'
  )

  nameInfoData = ShotgunORM.SgFieldSchemaInfo.createSchemaData(
    'AppWelcome',
    'name',
    ShotgunORM.SgField.RETURN_TYPE_TEXT,
    editable=False,
    label='Name'
  )

  appwelcomeFieldInfos = {
    'name': ShotgunORM.SgFieldSchemaInfo(nameInfoData),
    'id': ShotgunORM.SgFieldSchemaInfo(idInfoData)
  }

  AppWelcomeEntity = ShotgunORM.SgEntitySchemaInfo(
    schema,
    'AppWelcome',
    'AppWelcome',
    appwelcomeFieldInfos,
    {}
  )

  ShotgunORM.onEntitySchemaInfoCreate(AppWelcomeEntity)

  schemaData['AppWelcome'] = AppWelcomeEntity
  schemaData['Banner'] = BannerEntity

SCHEMA_CACHE_DIR = os.path.dirname(__file__).replace('\\', '/') + '/config/schema_caches'
SCHEMA_CACHE_DIR_ENV_VAR = 'PY_SHOTGUNORM_CACHE_PATH'

class SgSchema(object):
  '''
  Class that represents a Shotgun database schema.
  '''

  __lock__ = threading.RLock()
  __cache__ = {}

  __querytemplates__ = {
    'default': {},
    'empty': {}
  }

  __ignore_fields__ = {
    'global': {}
  }

  # This is the time that all functions which call wait on the buildEvent use
  # as a timeout value.
  BUILD_EVENT_TIMEOUT = 20

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

  def __repr__(self):
    return '<%s(url:"%s")>' % (self.__class__.__name__, self.url())

  def __init__(self, url):
    self.__lock = threading.RLock()
    self.__buildEvent = threading.Event()

    self.__buildEvent.clear()

    self._schema = {}
    self._url = url

    self.__valid = False
    self.__buildId = 0
    self.__timestamp = None
    self.__isBuilding = False
    self.__cachePath = None

  @classmethod
  def createSchema(cls, url):
    '''
    Creates a new schema for the specified URL and stores it in the global list
    of URL schemas.

    If a schema for the specified URL already exists then it will be returned
    instead.
    '''

    with cls.__lock__:
      cached = cls.findSchema(url)

      if cached != None:
        return cached

      result = cls(url)

      cls.__cache__[result.url().lower()] = result

      return result

  @classmethod
  def defaultEntityQueryFields(cls, sgQueryFieldTemplate, sgEntityType, fallBackTo='default'):
    '''
    Returns the list of default query fields for the specified Entity type and
    query template.
    '''

    try:
      return cls.__querytemplates__[sgQueryFieldTemplate][sgEntityType]
    except KeyError:
      if sgQueryFieldTemplate != 'empty' and fallBackTo != None and fallBackTo != sgQueryFieldTemplate:
        try:
          return cls.__querytemplates__[fallBackTo][sgEntityType]
        except KeyError:
          return []
      else:
        return []

  @classmethod
  def ignoreEntityField(cls, sgEntityType, sgField, sgConnection='global'):
    '''
    Registers a entity field so that it is ignored and not available to
    Entity objects.
    '''

    if cls.isFieldIgnored(sgEntityType, sgField, sgConnection):
      return

    connectionEntityFields = {}

    if cls.__ignore_fields__.has_key(sgConnection):
      connectionEntityFields = cls.__ignore_fields__[sgConnection]
    else:
      cls.__ignore_fields__[sgConnection] = connectionEntityFields

    if connectionEntityFields.has_key(sgEntityType):
      connectionEntityFields[sgEntityType].append(sgField)
    else:
      connectionEntityFields[sgEntityType] = [sgField]

  @classmethod
  def isFieldIgnored(cls, sgEntityType, sgField, sgConnection='global'):

    if sgConnection != 'global':
      if cls.isFieldIgnored(sgEntityType, sgField, 'global') == True:
        return True

    try:
      return sgField in cls.__ignore_fields__[sgConnection][sgEntityType]
    except:
      return False

  @classmethod
  def findSchema(cls, url):
    '''
    Returns the already created Schema of the specified URL.

    If a Schema does not exist for the URL then None is returned.
    '''

    with cls.__lock__:
      return cls.__cache__.get(url.lower(), None)

  @classmethod
  def registerDefaultQueryFields(cls, sgEntityType, sgQueryTemplates, sgFields):
    '''

    '''

    with cls.__lock__:
      if isinstance(sgQueryTemplates, str):
        sgQueryTemplates = [sgQueryTemplates]

      if isinstance(sgFields, str):
        sgFields = set(sgFields)

      for t in sgQueryTemplates:
        if not cls.__querytemplates__.has_key(t):
          cls.__querytemplates__[t] = {}

        if not isinstance(t, str):
          raise TypeError('expected a str in entity type list, got %s' % t)

        cls.__querytemplates__[t][sgEntityType] = set(sgFields)

  def _fromSG(self, sgConnection):
    '''
    Connects to Shotgun and prases the schema information.
    '''

    ShotgunORM.LoggerSchema.debug('    * Pulling schema from Shotgun')

    with ShotgunORM.SHOTGUN_API_LOCK:
      sgEntitySchemas = sgConnection._sg_schema_entity_read()
      sgEntityFieldSchemas = sgConnection._sg_schema_read()

    data = {}

    entityTypes = sorted(sgEntitySchemas.keys())

    for entityType in entityTypes:
      ShotgunORM.LoggerSchema.debug('        + Building Entity "%(entityName)s"', {'entityName': entityType})

      entitySchema = sgEntitySchemas[entityType]

      entityTypeLabel = entitySchema['name']['value']
      entityFieldSchemas = sgEntityFieldSchemas[entityType]

      entityInfo = ShotgunORM.SgEntitySchemaInfo.fromSg(self, entityType, entityTypeLabel, entityFieldSchemas)

      data[entityType] = entityInfo

      if entityInfo.isCustom():
        data[entityTypeLabel] = entityInfo

    ShotgunORM.LoggerSchema.debug('    * Building schema from Shotgun completed!')

    return {
      'data': data,
      'timestamp': str(datetime.datetime.now())
    }

  def _fromXML(self, path):
    '''
    Internal function.

    Parses a XML file containing the result of a SgSchema.export().
    '''

    ShotgunORM.LoggerSchema.debug('    * Parsing schema cache')

    tree = ET.parse(path)

    xmlRoot = tree.getroot()

    if xmlRoot.tag != 'SgSchema':
      raise RuntimeError('could not find SgSchema element in XML')

    ShotgunORM.LoggerSchema.debug('        schema version: %(schema_version)s', {'schema_version': xmlRoot.get('schema_version', 0)})
    ShotgunORM.LoggerSchema.debug('        timestamp: %(timestamp)s', {'timestamp': xmlRoot.get('timestamp', 0)})
    ShotgunORM.LoggerSchema.debug('        orm version: %(orm_version)s', {'orm_version': xmlRoot.get('orm_version', 0)})

    data = {}

    xmlEntities = xmlRoot.find('entities')

    if xmlEntities == None:
      raise RuntimeError('could not find entities element')

    buildId = self.buildId()

    for entity in xmlEntities:
      if entity.tag != 'SgEntity':
        raise RuntimeError('invalid tag "%s"' % entity.tag)

      ShotgunORM.LoggerSchema.debug('        + Building Entity "%(entityName)s"', {'entityName': entity.attrib.get('name')})

      entityInfo = ShotgunORM.SgEntitySchemaInfo.fromXML(self, entity)

      data[entityInfo.name()] = entityInfo

      if entityInfo.isCustom():
        data[entityInfo.label()] = entityInfo

    ShotgunORM.LoggerSchema.debug('    * Parsing schema cache complete!')

    return {
      'data': data,
      'timestamp': xmlRoot.get('timestamp')
    }

  def build(self, sgConnection, useCache=True):
    '''
    Builds the schema from shotgun.

    Returns a dictionary containing the schema info, cache id, and cache
    path if built from a cache xml file.
    '''

    schema = None
    cachePath = None

    url = self.url()
    urlLower = url.lower()

    if sgConnection.url().lower() != url:
      raise RuntimeError('connections url does not match schemas')

    if useCache == True:
      schemaCachePath = SCHEMA_CACHE_DIR
      schemaCachePathEnv = os.getenv(SCHEMA_CACHE_DIR_ENV_VAR, None)

      cacheFilename = None

      if url.startswith('https://'):
        cacheFilename = url[8:].lower() + '.xml'
      else:
        cacheFilename = url.lower() + '.xml'

      if schemaCachePathEnv != None:
        for i in schemaCachePathEnv.split(':'):
          if not os.path.exists(i):
            continue

          schemaCachePath = i + '/' + cacheFilename

          if os.path.exists(schemaCachePath):
            ShotgunORM.LoggerSchema.debug('    * Schema cache path found: "%(cachePath)s"', {'cachePath': schemaCachePath})

            try:
              schema = self._fromXML(schemaCachePath)

              cachePath = schemaCachePath

              break
            except Exception, e:
              ShotgunORM.LoggerSchema.error('        - Error loading XML')
              ShotgunORM.LoggerSchema.error(e)

    if schema == None:
      schema = self._fromSG(sgConnection)

    _entityFix(self, schema['data'])

    t = time.time()

    buildHash = hashlib.sha1()

    buildHash.update(str(t))

    return {
      'id': buildHash.hexdigest(),
      'cache_path': cachePath,
      'schema': schema['data'],
      'timestamp': schema['timestamp']
    }

  def buildCachePath(self):
    '''
    Returns the file path of the cache file used to generate the schema.

    Returns None if the schema was not built from a xml cache file.
    '''

    return self.__cachePath

  def buildId(self):
    '''
    Returns the build ID of the schema.

    Whenever a schema re-builds itself this ID number will be changed.

    The ID value is the sha1 hash of the time.time() the schema was built.
    '''

    return self.__buildId

  def _changed(self):
    '''
    Subclass portion of changed().

    Default does nothing.
    '''

    pass

  def changed(self):
    '''
    Called whenever the schemas info changes.

    Calls SgSchema._changed() and then ShotgunORM.onSchemaChanged() callback.
    '''

    self._changed()

    ShotgunORM.onSchemaChanged(self)

  def entityApiName(self, sgEntityType):
    '''
    Returns the true API name of the Entity type.

    This function is used to convert user friendly API names of custom Entities
    into their Shotgun api name.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    info = self.entityInfo(sgEntityType)

    if info == None:
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)

    return info.name()

  def entityInfo(self, sgEntityType):
    '''
    Returns the SgEntitySchemaInfo for the specified Entity type.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    return self._schema.get(sgEntityType, None)

  def entityInfos(self):
    '''
    Returns a dict containing all the Entity infos contained in the schema.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    return dict(self._schema)

  def entityLabelName(self, sgEntityType):
    '''
    Returns the user visible name of the Entity type.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    info = self.entityInfo(sgEntityType)

    return info.label()

  def entityTypes(self):
    '''
    Returns a list of Entity names contained in the schema.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    return sorted(self._schema.keys())

  def export(self, path):
    '''
    Exports the schema to the specified XML file.
    '''

    with self:
      if self.__cachePath != None:
        ShotgunORM.LoggerSchema.warn(
          'exporting schema when current schema was built from a cache file'
        )

      if not self.isInitialized():
        self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

        if not self.isInitialized():
          raise RuntimeError('schema has not been initialized')

      xmlData = self.toXML()

      tree = ET.ElementTree(xmlData)

      tree.write(path, 'utf-8')

      return True

  def initialize(self, sgConnection, thread=True):
    '''
    Builds the schema if it has not previously been built.
    '''

    if self.isInitialized():
      return

    self.refresh(sgConnection, thread)

  def isBuilding(self):
    '''
    Returns True if the schema is building.
    '''

    return self.__isBuilding

  def isBuiltFromCache(self):
    '''
    Returns True if the schema was built from a ShotgunORM xml cache.
    '''

    return self.__cachePath != None

  def isInitialized(self):
    '''
    Returns True if the schema is initialized.
    '''

    return self.__valid

  def isValidEntityType(self, sgEntityType):
    '''
    Returns True if the Entity type is a valid Entity name.
    '''

    return self.entityInfo(sgEntityType) != None

  def _refresh(self, sgConnection, event, refresh=False):
    '''

    '''

    with self:
      self.__buildEvent.clear()

      self.__isBuilding = True

      event.set()

      ignoreCache = self.isBuiltFromCache()

      try:
        data = self.build(
          sgConnection,
          not ignoreCache
        )
      finally:
        self.__isBuilding = False

        self.__buildEvent.set()

      self._schema = data['schema']
      self.__buildId = data['id']
      self.__cachePath = data['cache_path']
      self.__timestamp = data['timestamp']
      self.__valid = True

      self.changed()

  def refresh(self, sgConnection, thread=True):
    '''
    Refresh the schema from shotgun.

    ShotgunORM.onSchemaChanged() will be emitted afterwards.
    '''

    e = threading.Event()

    t = threading.Thread(
      target=self._refresh,
      name='%s.refresh()' % self,
      args=[
        sgConnection,
        e
      ]
    )

    t.setDaemon(True)

    t.start()

    if thread:
      e.wait()
    else:
      t.join()

  def timestamp(self):
    '''
    Returns the datetime that the schema was read from shotgun.
    '''

    return self.__timestamp

  def toXML(self):
    '''
    Returns an ElementTree representation of the schema.
    '''

    if not self.isInitialized():
      self.__buildEvent.wait(self.BUILD_EVENT_TIMEOUT)

      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

    xmlRoot = ET.Element(
      'SgSchema',
      orm_version=ShotgunORM.__version__,
      url=self.url(),
      timestamp=self.timestamp(),
      schema_version='1'
    )

    xmlEntities = ET.SubElement(xmlRoot, 'entities')

    entityInfos = self.entityInfos()

    for k in sorted(entityInfos.keys()):
      entityInfo = entityInfos[k]

      # Skip the duplicate custom entity infos.
      if entityInfo.name() != k:
        continue

      xmlEntities.append(entityInfo.toXML())

    return xmlRoot

  def url(self):
    '''
    Returns the Shotgun url the schema represents.
    '''

    return self._url
