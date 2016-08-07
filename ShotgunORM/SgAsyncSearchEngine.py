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
  'SgAsyncSearchResult'
]

# Python imports
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
    sgEntityType,
    sgFilters,
    sgFields,
    order,
    filterOperator,
    limit,
    retired_only,
    page,
    include_archived_projects,
    additional_filter_presets,
    isSingle,
    searchPosition
  ):
    '''
    Internal function for adding a search to the pending queue.

    This function does not obtain a lock!
    '''

    searchParameters = {
      'entity_type': sgEntityType,
      'filters': sgFilters,
      'fields': sgFields,
      'order': order,
      'filter_operator': filterOperator,
      'limit': limit,
      'retired_only': retired_only,
      'page': page,
      'include_archived_projects': include_archived_projects,
      'additional_filter_presets': additional_filter_presets,
      'single': isSingle
    }

    searchResult = SgAsyncSearchResult(searchParameters)

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
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None,
    isSingle=False
  ):
    '''
    Add the Shotgun search to the front of the async search queue.

    Returns a SgAsyncSearchResult.
    '''

    with self:
      return self.__addSearch(
        sgEntityType,
        sgFilters,
        sgFields,
        order,
        filterOperator,
        limit,
        retired_only,
        page,
        include_archived_projects,
        additional_filter_presets,
        isSingle,
        SG_ASYNC_ADD_SEARCH
      )

  def addToQueue(self, sgAsyncSearchResult):
    '''
    Add the SgAsyncSearchResult to the front of the async search queue.
    '''

    with self:
      self.__addSearchResult(
        sgAsyncSearchResult,
        SG_ASYNC_ADD_SEARCH
      )

  def appendSearchToQueue(
    self,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None,
    isSingle=False
  ):
    '''
    Add the Shotgun search to the back of the async search queue.

    Returns a SgAsyncSearchResult.
    '''

    with self:
      return self.__addSearch(
        sgEntityType,
        sgFilters,
        sgFields,
        order,
        filterOperator,
        limit,
        retired_only,
        page,
        include_archived_projects,
        additional_filter_presets,
        isSingle,
        SG_ASYNC_APPEND_SEARCH
      )

  def appendToQueue(self, sgAsyncSearchResult):
    '''
    Add the SgAsyncSearchResult to the back of the async search queue.
    '''

    with self:
      self.__addSearchResult(
        sgAsyncSearchResult,
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

class SgAsyncSearchResult(object):
  '''
  Class that represents an async Shotgun query.
  '''

  def __call__(self, timeout=None):
    return self.tryValue(timeout)

  def __init__(self, searchParameters):
    self.__event = threading.Event()
    self._result = None
    self.__errorException = None
    self.__errorMessage = None
    self.__searchParameters = searchParameters

    self.__event.clear()

    if self.__searchParameters['single']:
      del self.__searchParameters['page']
      del self.__searchParameters['limit']

  def _setResult(self, result, errorException=None, errorMessage=None):
    '''
    Internal function used to update the result with the data retrieved from
    Shotgun by the async search engines worker thread.
    '''

    if isinstance(result, list):
      self._result = list(result)
    else:
      self._result = result

    self.__errorException = errorException
    self.__errorMessage = errorMessage

    self.onResultSet()

    self.__event.set()

  def errorException(self):
    '''
    Returns the Exception object that was raised when the async search engine
    performed the search.
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

  def isReady(self):
    '''
    Returns True if the data for the search query has been retrieved from
    Shotgun and a call to value() will not block.
    '''

    return self.__event.isSet()

  def onResultSet(self):
    '''
    Called when the async search engine has returned the search result and
    value() will not block.

    Subclasses can implement this function to perform actions when the search
    result is ready.
    '''

    pass

  def searchParameters(self):
    '''
    Returns a dict containing the search parameters used when querying Shotgun
    to obtain the search results.
    '''

    return copy.deepcopy(self.__searchParameters)

  def tryValue(self, timeout=None):
    '''
    Try and return the search results, if the async search engine has not yet
    retrieved the results returns None.


    Args:
      * (int) timeout:
        Time in seconds to wait should the results have not yet been retrieved.
    '''

    if self.__event.wait(timeout):
      if isinstance(self._result, list):
        return list(self._result)
      else:
        return self._result
    else:
      return False

  def value(self):
    '''
    Return the search results, will block if the search is still pending in the
    async search engine.
    '''

    self.__event.wait()

    if isinstance(self._result, list):
      return list(self._result)
    else:
      return self._result

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

    try:
      ShotgunORM.LoggerAsyncSearchEngine.debug('    * Searching')

      searchParams = sgAsyncSearch.searchParameters()

      isSingle = searchParams['single']

      del searchParams['single']

      if isSingle:
        searchResult = con.findOne(
          **searchParams
        )
      else:
        searchResult = con.find(
          **searchParams
        )

      sgAsyncSearch._setResult(
        searchResult
      )

      ShotgunORM.LoggerAsyncSearchEngine.debug('    * Searching complete!')
    except Exception, e:
      ShotgunORM.LoggerAsyncSearchEngine.error(e)

      sgAsyncSearch._setResult(
        None,
        e,
        str(e)
      )
    finally:
      del sgAsyncSearch
      del con
