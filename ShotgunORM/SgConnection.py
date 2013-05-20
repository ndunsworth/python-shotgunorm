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
import os
import threading
import weakref
import webbrowser

# This module imports
import ShotgunORM

# Local
SG_CONNECTION_CACHE = {}

class SgConnectionMeta(type):
  '''
  Singleton metaclass for SgEntity objects.
  '''

  def __call__(cls, url, login, key):
    global SG_CONNECTION_CACHE

    cls.CACHE_LOCK.acquire()

    try:
      result = SG_CONNECTION_CACHE[url]['connections'][login][key]()

      if result != None:
        cls.CACHE_LOCK.release()

        return result
    except:
      pass

    try:
      result = cls.__new__(cls, url, login, key)

      if not SG_CONNECTION_CACHE.has_key(url):
        SG_CONNECTION_CACHE[url] = {
          'connections': {
            login: {
              key: result
            }
          }
        }
      elif not SG_CONNECTION_CACHE[url]['connections'].has_key(login):
        SG_CONNECTION_CACHE[url]['connections'][login] = {
          key: result
        }
      else:
        SG_CONNECTION_CACHE[url]['connections'][login][key] = weakref.ref(result)
    except:
      cls.CACHE_LOCK.release()

      raise

    cls.CACHE_LOCK.release()

    result.__init__(url, login, key)

    return result

class SgConnection(object):
  '''
  Class that represents a connection to Shotgun.

  This class is a singleton for a given url/login/key so multiple calls of
  the same info return the same SgConnection.
  '''

  CACHE_LOCK = threading.Lock()

  __metaclass__ = SgConnectionMeta

  def __eq__(self, item):
    if not isinstance(item, SgConnection):
      return False

    return (self.key() == item.key() and self.url() == item.url())

  def __ne__(self, item):
    return not (self == item)

  def __repr__(self):
    return '<SgConnection url:"%s", login:"%s">' % (self.url(), self.login())

  def __init__(self, url, login, key, sgQueryTemplate='default', sgClassFactory=None):
    self._url = str(url)
    self._login = str(login)
    self._key = str(key)

    self._connection = ShotgunORM.SHOTGUN_API.shotgun.Shotgun(
      self._url,
      self._login,
      self._key,
      connect=False
    )

    self._schema = None
    self._factory = None
    self._fieldQueryDefaults = sgQueryTemplate
    self._fieldQueryDefaultsFallback = 'default'

    schemas = ShotgunORM.SgSchema.__schemas__

    self._schema = ShotgunORM.SgSchema.createSchema(self._url, self)

    if sgClassFactory != None:
      if not isinstance(sgClassFactory, ShotgunORM.SgEntityClassFactory):
        raise TypeError('invalid value type factory "%s", expected SgEntityClassFactory' % type(factory).__name__)

      self._factory = sgClassFactory
    else:
      self._factory = ShotgunORM.SgEntityClassFactory.createFactory(self._url)

  def classFactory(self):
    '''
    Returns the SgEntityClassFactory used by this connection to create Entity
    objects.
    '''

    return self._factory

  def connect(self):
    '''
    Connects to the Shotgun db.
    '''

    self._connection.connect()

  def connection(self):
    '''
    Returns the Shotgun connection object.
    '''

    return self._connection

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
      result = set(schema.entityInfo(sgEntityType).fields())
    elif result == set(['none']):
      result = set([])

    return result

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

  def disconnect(self):
    '''
    Closes the connection to Shotgun.
    '''

    self._connection.close()

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

  def schema(self):
    '''
    Returns the SgSchema used by the connection.
    '''

    return self._schema

  def session(self, name='python', entitiesPersist=True):
    '''
    Returns a SgSession object for this connection.

    Args:
      * (str) name:
        Name of the session.

      * (bool) entitiesPersist:
        Enables Entity caching.
    '''
    if not self.schema().isInitialized():
      self.schema().initialize(self)

    if entitiesPersist:
      return ShotgunORM.SgSessionCached(self, name)
    else:
      return ShotgunORM.SgSession(self, name)

  def setFieldQueryTemplate(self, sgQueryTemplate):
    '''
    Sets the connections default field query template.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    if not isinstance(sgQueryTemplate, str):
      raise TypeError('expected a str for sgQueryTemplate, got %s' % type(sgQueryTemplate).__name__)

    self._fieldQueryDefaults = sgQueryTemplate

  def setFieldQueryTemplateFallback(self, sgQueryTemplate):
    '''
    Sets the connections default field query template fallback.

    Args:
      * (str) sgQueryTemplate:
        Name of the query template.
    '''

    self._fieldQueryDefaultsFallback = sgQueryTemplate

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
