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
  'SgSearchIterator'
]

# Python imports
import copy

class SgSearchIterator(object):
  '''
  Class used to iteratively retrieve a Shotgun search by page.
  '''

  def __iter__(self):
    class SgSearchIteratorIter(object):
      def __init__(self, sgSearchIterator):
        self.iter = sgSearchIterator
        self.results = []

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
    return '<SgSearchIterator limit=%d, page=%d>' % (
      self.__limit,
      self.__page
    )

  def __init__(
    self,
    sgConnection,
    sgEntityType,
    sgFilters=[],
    sgFields=None,
    order=None,
    filterOperator=None,
    limit=0,
    retired_only=False,
    page=1
  ):
    self.__connection = sgConnection
    self.__entity = sgEntityType
    self.__filter = copy.deepcopy(sgFilters)
    self.__fields = copy.deepcopy(sgFields)
    self.__order = copy.deepcopy(order)
    self.__filterOp = filterOperator
    self.__limit = min(500, int(limit))
    self.__retired = bool(retired_only)
    self.__page = max(1, int(page))
    self.__pageOrig = self.__page

    self.__results = []
    self.__hasMore = True

  def advance(self):
    '''
    Advances the search to the next batch of results.

    Does nothing if hasMore() returns False.
    '''

    if not self.hasMore():
      if len(self.__results) > 0:
        self.__results = []

      return False

    results = self.__connection.find(
      self.__entity,
      self.__filter,
      self.__fields,
      self.__order,
      self.__filterOp,
      self.__limit,
      self.__retired,
      self.__page
    )

    self.__hasMore = (
      self.__limit != 0 and len(results) == self.__limit
    )

    if self.__hasMore:
      self.__page += 1

    self.__results = results

    return True

  def connection(self):
    '''
    Returns the SgConnection the iterator is connected to.
    '''

    return self.__connection

  def hasMore(self):
    '''
    Returns True if there are possibly more results that can be returned from
    Shotgun.
    '''

    return self.__hasMore

  def next(self):
    '''
    Advances and returns the result of the next search batch.
    '''

    if self.advance():
      return list(self.__results)
    else:
      return []

  def limit(self):
    '''
    Returns the number of Entities that are being returned per batch query.
    '''

    return self.__limit

  def order(self):
    '''
    Returns the order filter of the search.
    '''

    return copy.deepcopy(self.__order)

  def page(self):
    '''
    Returns the page that advance() returned results from.
    '''

    return self.__page

  def reset(self):
    '''
    Rewinds the iterator so that the next call to advance will start from the
    begining.
    '''

    self.__page = self.__pageOrig
    self.__results = []
    self.__hasMore = True

  def results(self):
    '''
    Returns the results produced by advance().
    '''

    return list(self.__results)

  def retiredOnly(self):
    '''
    Returns the search argument value for returning retired Entities only.
    '''

    return self.__retired

  def searchFilter(self):
    '''
    Returns the Shotgun search filter that is used by the iterator.
    '''

    return copy.deepcopy(self.__filter)

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

    return self.__connection.summarize(
      self.__entity,
      self.__filter,
      [
        {
          'field': 'id',
          'type': 'count'
        }
      ]
    )['summaries']['id']
