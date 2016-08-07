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
  'SgEntityClassFactory'
]

# Python imports
import os
import threading
import weakref

# This module imports
import ShotgunORM

class SgEntityClassFactory(object):
  '''
  Class factory for building a SgConnections Entity objects.
  '''

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

    return False

  def __init__(self, sgConnection, sgEntityClasses={}):
    self.__lock = threading.RLock()

    self.__connection = weakref.ref(sgConnection)

    self._localEntityClasses = dict(sgEntityClasses)
    self._classCache = {}

    self._valid = False

  def build(self):
    '''
    Builds the factory.
    '''

    with self:
      ShotgunORM.LoggerFactory.debug('# BUILDING CLASS FACTORY')

      connection = self.connection()

      sgSchema = connection.schema()

      sgEntityInfos = sgSchema.entityInfos()

      newClassCache = {}

      for i in sorted(sgEntityInfos.keys()):
        entityInfo = sgEntityInfos[i]

        entityTypeName = entityInfo.name()
        entityTypeLabel = entityInfo.label()

        ShotgunORM.LoggerFactory.debug('    * Finding base class for Entity "%(entityType)s"', {'entityType': entityTypeLabel})

        entityBaseClass = None

        for level in [self._localEntityClasses, ShotgunORM.SgEntity.defaultEntityClasses()]:
          try:
            entityBaseClass = level[entityTypeName]

            break
          except KeyError:
            pass

          try:
            entityBaseClass = level[entityTypeLabel]

            break
          except KeyError:
            pass

        if entityBaseClass == None:
          try:
            entityBaseClass = ShotgunORM.SgEntity.defaultEntityClass('Entity')
          except:
            ShotgunORM.LoggerFactory.debug('        - Unable to find base class')

            raise RuntimeError('unable to find base class for Entity "%s"' % entityTypeName)


        fieldProps = {
          '__classinfo__': entityInfo,
          '__sg_connection__': self.__connection,
          '__sg_entity_name__': entityTypeName,
          '__sg_base_class__': entityBaseClass
        }

        ShotgunORM.LoggerFactory.debug('        + Using %(baseClass)s', {'baseClass': entityBaseClass})

        newEntityClass = type(entityTypeName, (entityBaseClass, ), fieldProps)

        newClassCache[entityTypeName] = newEntityClass

        if entityInfo.isCustom():
          self._classCache[entityTypeLabel] = newEntityClass

      self._classCache = newClassCache

      ShotgunORM.LoggerFactory.debug('# BUILDING CLASS FACTORY COMPLETE!')

      self._valid = True

  def connection(self):
    '''
    Returns the SgConnection the factory belongs to.
    '''

    return self.__connection()

  def createEntity(self, sgEntityType, sgData):
    '''
    Creates a new Entity object of type sgEntityType.
    '''

    entityClass = self._classCache.get(sgEntityType, None)

    if entityClass == None:
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)

    sgData = ShotgunORM.beforeEntityCreate(self.connection(), sgEntityType, sgData)

    result = entityClass()

    result.buildFields()
    result._fromFieldData(sgData)

    return result

  def initialize(self):
    '''
    Builds the factory.
    '''

    with self:
      if self.isInitialized():
        return True

      self.build()

  def isInitialized(self):
    '''
    Returns True if the factory has been built.
    '''

    return self._valid

  def entityClass(self, sgEntityType):
    '''
    Returns the class used by the specified Entity type.
    '''

    if not self._classCache.has_key(sgEntityType):
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)

    return self._classCache[sgEntityType]
