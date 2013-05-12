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

# This module imports
import ShotgunORM

class SgEntityClassFactory(object):
  '''
  Class factory for building a SgConnections Entity objects.
  '''

  __lock__ = threading.RLock()

  __factories__ = {}

  @classmethod
  def createFactory(self, sgFactoryName, sgEntityClasses={}):
    '''
    Creates and registers a new class factory.
    '''

    self.__lock__.acquire()

    try:
      sgFactoryName = sgFactoryName.lower()

      try:
        return self.__factories__[sgFactoryName]
      except:
        pass

      result = self(sgEntityClasses)

      self.__factories__[sgFactoryName] = result

      return result
    finally:
      self.__lock__.release()

  def __init__(self, sgEntityClasses={}):
    self._lock = threading.RLock()

    self._localEntityClasses = dict(sgEntityClasses)
    self._classCache = {}

    self._valid = False

  def build(self, sgEntityInfos):
    '''

    '''

    self._lock.acquire()

    try:
      ShotgunORM.LoggerFactory.debug('# BUILDING CLASS FACTORY')

      newClassCache = {}

      for i in sorted(sgEntityInfos.keys()):
        entityInfo = sgEntityInfos[i]

        entityTypeName = entityInfo.name()
        entityTypeLabel = entityInfo.label()

        ShotgunORM.LoggerFactory.debug('    * Finding base class for Entity "%(entityType)s"', {'entityType': entityTypeLabel})

        entityBaseClass = None

        for level in [self._localEntityClasses, ShotgunORM.SgEntity.__defaultentityclasses__]:
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
            entityBaseClass = ShotgunORM.SgEntity.__defaultentityclasses__['Entity']
          except:
            ShotgunORM.LoggerFactory.debug('        - Unable to find base class')

            raise RuntimeError('unable to find base class for Entity "%s"' % entityTypeName)


        fieldProps = {
          '__classinfo__': entityInfo
        }

        ShotgunORM.LoggerFactory.debug('        + Using %(baseClass)s', {'baseClass': entityBaseClass})

        newEntityClass = type(entityTypeName, (entityBaseClass, ), fieldProps)

        newClassCache[entityTypeName] = newEntityClass

        if entityInfo.isCustom():
          self._classCache[entityTypeLabel] = newEntityClass

      self._classCache = newClassCache

      ShotgunORM.LoggerFactory.debug('# BUILDING CLASS FACTORY COMPLETE!')
    finally:
      self._lock.release()

  def initialize(self, sgSchema):
    '''
    Builds the factory.
    '''

    self._lock.acquire()

    try:
      if self.isInitialized():
        return True

      self.rebuild(sgSchema)

      self._valid = True
    finally:
      self._lock.release()

  def isInitialized(self):
    '''

    '''

    return self._valid

  def createEntity(self, sgSession, sgEntityType, sgData):
    '''
    Creates a new Entity object of type sgEntityType.
    '''

    entityClass = self._classCache.get(sgEntityType, None)

    if entityClass == None:
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)

    result = entityClass(sgSession)

    result.buildFields()
    result._fromFieldData(sgData)

    ShotgunORM.onEntityCreate(result)

    return result

  def entityClass(self, sgEntityType):
    '''
    Returns the class used by the specified Entity type.
    '''

    try:
      return self._classCache[sgEntityType]
    except:
      raise RuntimeError('unknown Entity type "%s"' % sgEntityType)
