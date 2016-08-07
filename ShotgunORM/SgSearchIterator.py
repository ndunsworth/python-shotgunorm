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
  'SgAbstractSearchIterator',
  'SgBufferedSearchIterator',
  'SgSearchIterator'
]

# Python imports
import abc
import copy

class SgAbstractSearchIterator(object):
  '''
  Abstract search iterator, base class for all search iterators.
  '''

  __metaclass__ = abc.ABCMeta

  def __iter__(self):
    class SgSearchIteratorIter(object):
      def __init__(self, sgSearchIterator):
        self.iter = sgSearchIterator
        self.results = sgSearchIterator.results()

      def next(self):
        if len(self.results) > 0:
          return self.results.pop(0)

        if self.iter.hasMore():
          self.results = self.iter.next()

          if len(self.results) > 0:
            return self.results.pop(0)

        raise StopIteration

    return SgSearchIteratorIter(self)

  def __repr__(self):
    return '<%s connection=%s, limit=%d, page=%d>' % (
      self.__class__.__name__,
      self._connection,
      self._limit,
      self._page - 1
    )

  def __init__(
    self,
    sgConnection,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    self._additional_filter_presets = copy.deepcopy(additional_filter_presets)
    self._archived_projects = bool(include_archived_projects)
    self._connection = sgConnection
    self._entityType = sgEntityType
    self._filter = copy.deepcopy(sgFilters)
    self._fields = copy.deepcopy(sgFields)
    self._order = copy.deepcopy(order)
    self._filterOp = copy.deepcopy(filterOperator)
    self._limit = min(500, int(limit))
    self._retiredOnly = bool(retired_only)
    self._page = max(1, int(page))
    self._pageOrig = self._page

    self._page -= 1

  @abc.abstractmethod
  def _advance(self):
    '''
    Subclass portion of advance()

    Subclasses must implement this method and return True if advancement
    was successful otherwise return False.
    '''

    return False

  def advance(self):
    '''
    Advances the search to the next batch of results.
    '''

    if self.hasMore():
      if self._advance():
        self._page += 1

        return True
      else:
        return False
    else:
      self._clear()

      return False

  def _clear(self):
    '''
    Subclasses can implement this function to clear any results returned by a
    previous advance() call.
    '''

    pass

  def connection(self):
    '''
    Returns the SgConnection the iterator is connected to.
    '''

    return self._connection

  def entityType(self):
    '''
    Returns the name of the Entity type the seach returns.
    '''

    return self._entityType

  def fields(self):
    '''
    Returns a list of field names the the search result will populate for the
    Entity objects.
    '''

    if self._fields == None:
      return []
    else:
      return list(self._fields)

  def filter(self):
    '''
    Returns the Shotgun search filter that is used by the iterator.
    '''

    return copy.deepcopy(self._filter)

  def filterOperator(self):
    '''
    Returns the Shotgun search filter operator that is used by the iterator.
    '''

    return copy.deepcopy(self._filterOp)

  def hasLess(self):
    '''

    '''

    return self._page > self._pageOrig

  @abc.abstractmethod
  def hasMore(self):
    '''
    Returns True if there are possibly more results that can be returned from
    Shotgun.
    '''

    return False

  def next(self):
    '''
    Advances and returns the result of the next search batch.
    '''

    self.advance()

    return self.results()

  def limit(self):
    '''
    Returns the number of Entities that are being returned per batch query.
    '''

    return self._limit

  def order(self):
    '''
    Returns the order filter of the search.
    '''

    return copy.deepcopy(self._order)

  def page(self):
    '''
    Returns the page that advance() returned results from.
    '''

    return self._page

  def previous(self):
    '''

    '''

    self.rewind()

    return self.results()

  def reset(self):
    '''
    Rewinds the iterator so that the next call to advance will start from the
    begining.

    Subclasses should implement the _reset() method and not override this.
    '''

    self._clear()

    self._page = self._pageOrig - 1

    self._reset()

  @abc.abstractmethod
  def results(self):
    '''
    Returns the results produced by advance().
    '''

    return []

  def retiredOnly(self):
    '''
    Returns the search argument value for returning retired Entities only.
    '''

    return self._retiredOnly

  @abc.abstractmethod
  def _rewind(self):
    '''

    '''

    return False

  def rewind(self):
    '''
    Advances the search to the next batch of results.
    '''

    if self.hasLess():
      if self._rewind():
        self._page -= 1

        return True
      else:
        return False
    else:
      self.reset()

      return False

  def summarySize(self):
    '''
    Returns the current number of Entities the search would produce.

    Note:
      This value can not be assumed to be absolute as during the search
      iteration new Entities can be added which would be returned by the search
      results as well as Entities can be deleted during the process.

      This value should only be used as a guesstimate for the number of entries
      that will be produced.
    '''

    return self._connection.summarize(
      self._entityType,
      self._filter,
      [
        {
          'field': 'id',
          'type': 'count'
        }
      ]
    )['summaries']['id']

class SgSearchIterator(SgAbstractSearchIterator):
  '''
  Class used to iteratively retrieve a Shotgun search by page.
  '''

  def __init__(
    self,
    sgConnection,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    super(SgSearchIterator, self).__init__(
      sgConnection,
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filterOperator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

    self.__results = []
    self.__hasMore = True

  def _advance(self):
    results = self._connection.find(
      self._entityType,
      self._filter,
      self._fields,
      self._order,
      self._filterOp,
      self._limit,
      self._retiredOnly,
      self._page + 1,
      self._archived_projects,
      self._additional_filter_presets
    )

    self.__hasMore = (
      self._limit != 0 and len(results) == self._limit
    )

    self.__results = results

    return True

  def _clear(self):
    self.__results = []
    self.__hasMore = False

  def hasMore(self):
    '''
    Returns True if there are possibly more results that can be returned from
    Shotgun.
    '''

    return self.__hasMore

  def _reset(self):
    self.__hasMore = True

  def results(self):
    '''
    Returns the results produced by advance().
    '''

    return list(self.__results)

  def _rewind(self):
    '''

    '''

    results = self._connection.find(
      self._entityType,
      self._filter,
      self._fields,
      self._order,
      self._filterOp,
      self._limit,
      self._retiredOnly,
      self._page - 1,
      self._archived_projects,
      self._additional_filter_presets
    )

    self.__hasMore = (
      self._limit != 0 and len(results) == self._limit
    )

    self.__results = results

    return True

class SgBufferedSearchIterator(SgAbstractSearchIterator):
  '''
  Class used to iteratively retrieve a Shotgun search by page.

  Buffers the search so that it is always one batch ahead.
  '''

  def __init__(
    self,
    sgConnection,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=100,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    super(SgBufferedSearchIterator, self).__init__(
      sgConnection,
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filterOperator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

    self.__prevResult = None
    self.__currentResult = None
    self.__nextResult = self.createAsyncResult(
      self._entityType,
      self.filter(),
      self.fields(),
      self.order(),
      self.filterOperator(),
      self._limit,
      self._retiredOnly,
      self._page + 1,
      self._archived_projects,
      self._additional_filter_presets
    )

  def _advance(self):
    self.__prevResult = self.__currentResult
    self.__currentResult = self.__nextResult

    results = self.__currentResult.value()

    if results == None:
      self.__nextResult = None

      return False

    if len(results) == self._limit:
      self.__nextResult = self.createAsyncResult(
        self._entityType,
        self.filter(),
        self.fields(),
        self.order(),
        self.filterOperator(),
        self._limit,
        self._retiredOnly,
        self._page + 2,
        self._archived_projects,
        self._additional_filter_presets
      )
    else:
      self.__nextResult = None

    return True

  def createAsyncResult(
    self,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=0,
    retired_only=False,
    page=1,
    include_archived_projects=True,
    additional_filter_presets=None
  ):
    '''
    Returns a new SgAsyncSearchResult used by advance.

    Subclasses can implement this function to return there own custom class of
    SgAsyncSearchResult.
    '''

    return self._connection.findAsync(
      sgEntityType,
      sgFilters,
      sgFields,
      order,
      filterOperator,
      limit,
      retired_only,
      page,
      include_archived_projects,
      additional_filter_presets
    )

  def hasMore(self):
    '''
    Returns True if there are possibly more results that can be returned from
    Shotgun.
    '''

    return self.__nextResult != None

  def previous(self):
    '''

    '''

    if self.rewind() == True:
      return self.results()
    else:
      return []

  def _reset(self):
    self.__prevResult = None
    self.__currentResult = None
    self.__nextResult = self.createAsyncResult(
      self._entityType,
      self.filter(),
      self.fields(),
      self.order(),
      self.filterOperator(),
      self._limit,
      self._retiredOnly,
      self._page + 1,
      self._archived_projects,
      self._additional_filter_presets
    )

  def results(self):
    '''
    Returns the results produced by advance().
    '''

    if self.__currentResult == None or self.__currentResult.hasError():
      return []
    else:
      return self.__currentResult.value()

  def _rewind(self):
    '''

    '''

    self.__nextResult = self.__currentResult
    self.__currentResult = self.__prevResult

    if self._page != self._pageOrig:
      self.__prevResult = self.createAsyncResult(
        self._entityType,
        self.filter(),
        self.fields(),
        self.order(),
        self.filterOperator(),
        self._limit,
        self._retiredOnly,
        self._page - 2,
        self._archived_projects,
        self._additional_filter_presets
      )
    else:
      self.__prevResult = None

    return True
