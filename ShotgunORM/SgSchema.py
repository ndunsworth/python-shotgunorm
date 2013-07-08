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
import os
import threading
import weakref

from xml.etree import ElementTree as ET

# This module imports
import ShotgunORM

def _entityFix(schemaData):
  '''
  Returns Entities that dont exist in the API but fields return them as values.

  * Currently returns *

    1: Banner Entity
    2: AppWelcome Entity
  '''

  nameData = {
    'default_value': None,
    'doc': '',
    'editable': False,
    'label': 'Name',
    'name': 'name',
    'parent': 'Banner',
    'required': False,
    'return_type': ShotgunORM.SgField.RETURN_TYPE_TEXT,
    'return_type_name': 'text',
    'summary_info': None,
    'value_types': None,
    'valid_values': []
  }

  idData = {
    'default_value': None,
    'doc': '',
    'editable': False,
    'expression': None,
    'label': 'Id',
    'name': 'id',
    'parent': 'Banner',
    'required': False,
    'return_type': ShotgunORM.SgField.RETURN_TYPE_INT,
    'return_type_name': 'number',
    'summary_info': None,
    'value_types': None,
    'valid_values': []
  }

  bannerFieldInfos = {
    'name': ShotgunORM.SgFieldInfo(nameData),
    'id': ShotgunORM.SgFieldInfo(idData)
  }

  BannerEntity = ShotgunORM.SgEntityInfo('Banner', 'Banner', bannerFieldInfos)

  nameData = {
    'default_value': None,
    'doc': '',
    'editable': False,
    'label': 'Name',
    'name': 'name',
    'parent': 'AppWelcome',
    'required': False,
    'return_type': ShotgunORM.SgField.RETURN_TYPE_TEXT,
    'return_type_name': 'text',
    'summary_info': None,
    'value_types': None,
    'valid_values': []
  }

  idData = {
    'default_value': None,
    'doc': '',
    'editable': False,
    'label': 'Id',
    'name': 'id',
    'parent': 'AppWelcome',
    'required': False,
    'return_type': ShotgunORM.SgField.RETURN_TYPE_INT,
    'return_type_name': 'number',
    'summary_info': None,
    'value_types': None,
    'valid_values': []
  }

  bannerFieldInfos = {
    'name': ShotgunORM.SgFieldInfo(nameData),
    'id': ShotgunORM.SgFieldInfo(idData)
  }

  AppWelcomeEntity = ShotgunORM.SgEntityInfo('AppWelcome', 'AppWelcome', bannerFieldInfos)

  schemaData['AppWelcome'] = AppWelcomeEntity
  schemaData['Banner'] = BannerEntity

SCHEMA_CACHE_DIR = os.path.dirname(__file__).replace('\\', '/') + '/config/schema_caches'

class SgSchema(object):
  '''
  Class that represents a Shotgun database schema.
  '''

  __lock__ = threading.RLock()
  __cache__ = {}

  __querytemplates__ = {
    'default': {}
  }

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

  def __repr__(self):
    return '<%s(url:"%s")>' % (self.__class__.__name__, self.url())

  def __init__(self, url):
    self.__lock = threading.RLock()

    self._schema = {}
    self._url = url

    self.__valid = False

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

      urlLower = result.url().lower()

      cls.__cache__[urlLower] = result

      return result

  @classmethod
  def findSchema(cls, url):
    '''
    Returns the already created Schema of the specified URL.

    If a Schema does not exist for the URL then None is returned.
    '''

    with cls.__lock__:
      urlLower = url.lower()

      try:
        return cls.__cache__[urlLower]
      except KeyError:
        return None

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

  @classmethod
  def defaultEntityQueryFields(cls, sgQueryFieldTemplate, sgEntityType, fallBackTo='default'):
    '''
    Returns the list of default query fields for the specified Entity type and
    query template.
    '''

    try:
      return cls.__querytemplates__[sgQueryFieldTemplate][sgEntityType]
    except KeyError:
      if fallBackTo != None:
        try:
          return cls.__querytemplates__[fallBackTo][sgEntityType]
        except KeyError:
          return []
      else:
        return []

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

    result = {}

    xmlEntities = xmlRoot.find('entities')

    if xmlEntities == None:
      raise RuntimeError('could not find entities element')

    for entity in xmlEntities:
      if entity.tag != 'SgEntity':
        raise RuntimeError('invalid tag "%s"' % entity.tag)

      ShotgunORM.LoggerSchema.debug('        + Building Entity "%(entityName)s"', {'entityName': entity.attrib.get('name')})

      entityInfo = ShotgunORM.SgEntityInfo.fromXML(entity)

      result[entityInfo.name()] = entityInfo

      if entityInfo.isCustom():
        result[entityInfo.label()] = entityInfo

    ShotgunORM.LoggerSchema.debug('    * Parsing schema cache complete!')

    return result

  def _fromSG(self, sgConnection):
    '''
    Connects to Shotgun and prases the schema information.
    '''

    ShotgunORM.LoggerSchema.debug('    * Pulling schema from Shotgun')

    with ShotgunORM.SHOTGUN_API_LOCK:
      sgEntitySchemas = sgConnection.connection().schema_entity_read()
      sgEntityFieldSchemas = sgConnection.connection().schema_read()

    entityInfos = {}

    entityTypes = sorted(sgEntitySchemas.keys())

    for entityType in entityTypes:
      ShotgunORM.LoggerSchema.debug('        + Building Entity "%(entityName)s"', {'entityName': entityType})

      entitySchema = sgEntitySchemas[entityType]

      entityTypeLabel = entitySchema['name']['value']
      entityFieldSchemas = sgEntityFieldSchemas[entityType]

      entityInfo = ShotgunORM.SgEntityInfo.fromSg(entityType, entityTypeLabel, entityFieldSchemas)

      entityInfos[entityType] = entityInfo

      if entityInfo.isCustom():
        entityInfos[entityTypeLabel] = entityInfo

    ShotgunORM.LoggerSchema.debug('    * Building schema from Shotgun completed!')

    return entityInfos

  def build(self, sgConnection):
    '''
    Builds the schema.

    If the schema has previously been built this will cause the schema to
    rebuild itself.

    See SgSchema.initialize() if you only want to make sure the schema is built.
    '''

    with self:
      ShotgunORM.LoggerSchema.debug('# BUILDING SCHEMA "%(url)s"', {'url': self._url})

      loadedCache = False

      schemaCachePath = SCHEMA_CACHE_DIR

      newSchema = {}

      url = self.url()
      urlLower = url.lower()

      if sgConnection.url().lower() != url:
        raise RuntimeError('connections url does not match schemas')

      if url.startswith('https://'):
        schemaCachePath += '/' + url[8:] + '.xml'
      else:
        schemaCachePath += '/' + url.lower() + '.xml'

      if os.path.exists(schemaCachePath):
        ShotgunORM.LoggerSchema.debug('    * Schema cache path found: "%(cachePath)s"', {'cachePath': schemaCachePath})

        try:
          newSchema = self._fromXML(schemaCachePath)

          loadedCache = True
        except Exception, e:
          ShotgunORM.LoggerSchema.error('        - Error loading XML, falling back to Shotgun database')
          ShotgunORM.LoggerSchema.error(e)

      if loadedCache == False:
        newSchema = self._fromSG(sgConnection)

      _entityFix(newSchema)

      self._schema = newSchema

      self.__valid = True

      self.changed()

  def _changed(self):
    '''
    Sub-class portion of changed().

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
      raise RuntimeError('schema has not been initialized')

    info = self.entityInfo(sgEntityType)

    if info == None:
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)

    return info.name()

  def entityInfo(self, sgEntityType):
    '''
    Returns the SgEntityInfo for the specified Entity type.
    '''

    if not self.isInitialized():
      raise RuntimeError('schema has not been initialized')

    return self._schema.get(sgEntityType, None)

  def entityInfos(self):
    '''
    Returns a dict containing all the Entity infos contained in the schema.
    '''

    if not self.isInitialized():
      raise RuntimeError('schema has not been initialized')

    return dict(self._schema)

  def entityLabelName(self, sgEntityType):
    '''
    Returns the user visible name of the Entity type.
    '''

    if not self.isInitialized():
      raise RuntimeError('schema has not been initialized')

    info = self.entityInfo(sgEntityType)

    return info.label()

  def entityTypes(self):
    '''
    Returns a list of Entity names contained in the schema.
    '''

    if not self.isInitialized():
      raise RuntimeError('schema has not been initialized')

    return sorted(self._schema.keys())

  def export(self, path):
    '''
    Exports the schema to the specified XML file.
    '''

    with self:
      if not self.isInitialized():
        raise RuntimeError('schema has not been initialized')

      xmlData = self.toXML()

      tree = ET.ElementTree(xmlData)

      tree.write(path)

      return True

  def initialize(self, sgConnection):
    '''
    Builds the schema if it has not previously been built.
    '''

    with self:
      if self.isInitialized():
        return True

      self.build(sgConnection)

  def isInitialized(self):
    '''
    Returns True if the schema is initialized.
    '''

    return self.__valid

  def toXML(self):
    '''
    Returns an ElementTree representation of the schema.
    '''

    if not self.isInitialized():
      raise RuntimeError('schema has not been initialized')

    xmlRoot = ET.Element(
      'SgSchema',
      orm_version=ShotgunORM.__version__,
      schema_version='1',
      url=self.url()
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
