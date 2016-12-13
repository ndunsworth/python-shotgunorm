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
  'SgAsyncSearchEngine',
  'SgAsyncResult',
  'SgAsyncEntitySearchResult',
  'SgAsyncTextSearchResult'
]

# Python imports
from abc import abstractmethod

import copy
import threading
import weakref

# This module imports
import ShotgunORM

SG_ASYNC_ADD_SEARCH = 0
SG_ASYNC_APPEND_SEARCH = 1

class SgAsyncSearchEngine(object):
  '''
  Class that represents an asynchronous Shotgun search engine.
  '''

  def __del__(self):
    try:
      self.shutdown()
    except:
      pass

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

    return False

  def __repr__(self):
    connection = self.connection()

    if connection == None:
      return '<SgAsyncSearchEngine>'

    return '<SgAsyncSearchEngine url:"%(url)s", script:"%(script)s">' % {
      'url': connection.url(),
      'script': connection.scriptName()
    }

  def __init__(self, sgConnection):
    self.__connection = weakref.ref(sgConnection)
    self.__lock = threading.Lock()
    self.__qEvent = threading.Event()
    self.__qShutdownEvent = threading.Event()
    self.__pendingQueries = []

    self.__engineThread = threading.Thread(
      name=self.__repr__(),
      target=SgAsyncSearchEngineWorker,
      args = [
        self.__connection,
        self.__lock,
        self.__qEvent,
        self.__qShutdownEvent,
        self.__pendingQueries
      ]
    )

    self.__engineThread.setDaemon(True)

  def connection(self):
    '''
    Returns the connection the engine belongs to.
    '''

    return self.__connection()

  def __addSearch(
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
    additional_filter_presets,
    sgQueryFieldTemplate,
    isSingle,
    searchPosition
  ):
    '''
    Internal function for adding a search to the pending queue.

    This function does not obtain a lock!
    '''

    params = ShotgunORM.SgSearchParameters(
      entity_type,
      filters,
      fields,
      order,
      filter_operator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets,
      sgQueryFieldTemplate,
      self.connection()
    )

    searchResult = SgAsyncEntitySearchResult(params, isSingle)

    self.__addSearchResult(searchResult, searchPosition)

    return searchResult

  def __addSearchResult(self, searchResult, searchPosition):
    '''

    '''

    if searchPosition == SG_ASYNC_ADD_SEARCH:
      self.__pendingQueries.insert(
        0,
        weakref.ref(searchResult)
      )
    else:
      self.__pendingQueries.append(
        weakref.ref(searchResult)
      )

    self.__qEvent.set()

  def addSearchToQueue(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None,
    sgQueryFieldTemplate=None,
    isSingle=False
  ):
    '''
    Add the Shotgun search to the front of the async search queue.

    Returns a SgAsyncEntitySearchResult.
    '''

    with self:
      return self.__addSearch(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        limit,
        retired_only,
        page,
        include_archived_projects,
        additional_filter_presets,
        sgQueryFieldTemplate,
        SG_ASYNC_ADD_SEARCH
      )

  def addToQueue(self, sgAsyncResult):
    '''
    Add the SgAsyncResult to the front of the async search queue.
    '''

    with self:
      self.__addSearchResult(
        sgAsyncResult,
        SG_ASYNC_ADD_SEARCH
      )

  def appendSearchToQueue(
    self,
    entity_type,
    filters=[],
    fields=None,
    order=None,
    filter_operator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None,
    sgQueryFieldTemplate=None,
    isSingle=False
  ):
    '''
    Add the Shotgun search to the back of the async search queue.

    Returns a SgAsyncEntitySearchResult.
    '''

    with self:
      return self.__addSearch(
        entity_type,
        filters,
        fields,
        order,
        filter_operator,
        limit,
        retired_only,
        page,
        include_archived_projects,
        additional_filter_presets,
        sgQueryFieldTemplate,
        isSingle,
        SG_ASYNC_APPEND_SEARCH
      )

  def appendToQueue(self, sgAsyncResult):
    '''
    Add the SgAsyncResult to the back of the async search queue.
    '''

    with self:
      self.__addSearchResult(
        sgAsyncResult,
        SG_ASYNC_APPEND_SEARCH
      )

  def pending(self):
    '''
    Returns the number of pending queries.
    '''

    return len(self.__pendingQueries)

  def shutdown(self):
    '''
    Shutdown the engine.
    '''

    if self.__engineThread.isAlive():
      self.__qEvent.set()
      self.__qShutdownEvent.wait()

  def start(self):
    '''
    Starts the engines background thread.
    '''

    self.__engineThread.start()

class SgAsyncResult(object):
  '''

  '''

  BATCH_COMMIT = 0
  ENTITY_SEARCH = 1
  TEXT_SEARCH = 2

  def __call__(self, timeout=None):
    return self.tryValue(timeout)

  def __init__(self):
    self._result = None

    self.__event = threading.Event()
    self.__errorException = None
    self.__errorMessage = None
    self.__pending = False
    self.__connection = None

    self.__event.clear()

  def __setResult(
    self,
    result,
    errorException=None,
    errorMessage=None
  ):
    '''
    Internal function used to update the result with the data retrieved
    from Shotgun by the async search engines worker thread.
    '''

    self._result = result

    self.__errorException = errorException
    self.__errorMessage = errorMessage
    self.__pending = False

    self.onResultSet()

    self.__event.set()

  @abstractmethod
  def _execute(self, sgConnection):
    '''

    '''

    return None

  def execute(self, sgConnection):
    '''

    '''

    try:
      result = self._execute(sgConnection)

      self.__setResult(result)

      self.__connection = weakref.ref(sgConnection)
    except Exception, e:
      self.__setResult(None, e, str(e))

      ShotgunORM.LoggerAsyncSearchEngine.error(e)

  @abstractmethod
  def copy(self):
    '''

    '''

    raise NotImplementedError()

  def connection(self):
    '''
    Returns the Shotgun connection used to preform the search.
    '''

    if self.__connection == None:
      return None
    else:
      return self.__connection()

  def errorException(self):
    '''
    Returns the Exception object that was raised when the async search
    engine performed the search.
    '''

    return self.__errorException

  def errorMessage(self):
    '''
    Returns the Exception error as a string.
    '''

    return self.__errorMessage

  def hasError(self):
    '''
    Returns True if an error occured while processing the search result.
    '''

    return self.__errorException != None

  def isPending(self):
    '''
    Returns True if the result has yet to be processed.
    '''

    return self.__pending

  def isReady(self):
    '''
    Returns True if the data for the search query has been retrieved
    from Shotgun and a call to value() will not block.
    '''

    return self.__event.isSet()

  def onResultSet(self):
    '''
    Called when the async search engine has returned the search result
    and value() will not block.

    Subclasses can implement this function to perform actions when the
    search result is ready.
    '''

    pass

  def tryValue(self, timeout=None):
    '''
    Try and return the search results, if the async search engine has
    not yet retrieved the results returns None.


    Args:
      * (int) timeout:
        Time in seconds to wait should the results have not yet been
        retrieved.
    '''

    if self.__event.wait(timeout):
      return self._result
    else:
      return None

  @abstractmethod
  def type(self):
    '''

    '''

    raise NotImplementedError()

  def value(self):
    '''
    Return the search results, will block if the search is still pending
    in the async search engine.
    '''

    self.__event.wait()

    return self._result

class SgAsyncEntitySearchResult(SgAsyncResult):
  '''
  Class that represents an async Shotgun query.
  '''

  def __init__(self, sgSearchParameters, isSingle=False):
    super(SgAsyncEntitySearchResult, self).__init__()

    self._params = sgSearchParameters
    self._single = bool(isSingle)

  def _execute(self, sgConnection):
    '''

    '''

    params = self._params.parameters()

    if self.isSingle():
      return sgConnection.findOne(**params)
    else:
      return sgConnection.find(**params)

  def copy(self):
    '''
    Returns a copy of this SgAsyncEntitySearchResult.
    '''

    return SgAsyncEntitySearchResult(
      self._params.copy(),
      self._single
    )

  def isSingle(self):
    '''

    '''

    return self._single

  def parameters(self):
    '''
    Returns a dict containing the search parameters used when querying
    Shotgun to obtain the search results.
    '''

    return self._params.copy()

  def type(self):
    '''
    Returns the SgAsyncResult type ENTITY_SEARCH.
    '''

    return SgAsyncResult.ENTITY_SEARCH

  def size(self):
    '''

    '''

    self.__event.wait()

    if isinstance(self.__result, list):
      return len(self.__result)
    else:
      return 1

class SgAsyncTextSearchResult(SgAsyncResult):
  '''

  '''

  def __init__(self, text, entity_types, project_ids=None, limit=None):
    super(SgAsyncTextSearchResult, self).__init__()

    self._params = ShotgunORM.SgTextSearchParameters(
      text,
      entity_types,
      project_ids,
      limit
    )

  def _execute(self, sgConnection):
    '''

    '''

    return sgConnection.textSearch(**self._params.parameters())

  def copy(self):
    '''
    Returns a copy of this SgAsyncTextSearchResult.
    '''

    return SgAsyncTextSearchResult(**self._params.parameters())

  def entityTypes(self):
    '''
    Returns a dict containing search type filters.
    '''

    return self._params.entityTypes()

  def limit(self):
    '''
    Returns the search limit.
    '''

    return self._params.limit()

  def projectIds(self):
    '''
    Returns a list of project ids
    '''

    return self._params.projectIds()

  def text(self):
    '''
    Returns the search filter text.
    '''

    return self._params.text()

  def type(self):
    '''
    Returns the SgAsyncResult type TEXT_SEARCH.
    '''

    return SgAsyncResult.TEXT_SEARCH

def SgAsyncSearchEngineWorker(
  connection,
  lock,
  event,
  eventShutdown,
  pendingQueries
):
  while True:
    event.wait()

    if len(pendingQueries) <= 0:
      try:
        ShotgunORM.LoggerAsyncSearchEngine.debug(
          'Stopping because engine set event and pendingQueries size is zero'
        )
      except:
        pass

      eventShutdown.set()

      return

    sgAsyncSearch = None

    with lock:
      ShotgunORM.LoggerAsyncSearchEngine.debug(
        'Queue: job 1 of %(size)d',
        {'size': len(pendingQueries)}
      )

      sgAsyncSearch = pendingQueries.pop(0)

      if len(pendingQueries) <= 0:
        event.clear()

    sgAsyncSearch = sgAsyncSearch()

    if sgAsyncSearch == None:
      continue

    ShotgunORM.LoggerAsyncSearchEngine.debug('    * Processing')

    con = connection()

    if con == None:
      try:
        ShotgunORM.LoggerAsyncSearchEngine.debug(
          '    * Stopping because connection not found'
        )
      except:
        pass

      return

    search_type = sgAsyncSearch.type()

    ShotgunORM.LoggerAsyncSearchEngine.debug('    * Executing')

    try:
      sgAsyncSearch.execute(con)
    finally:
      del sgAsyncSearch
      del con

    ShotgunORM.LoggerAsyncSearchEngine.debug('    * Executing complete!')
