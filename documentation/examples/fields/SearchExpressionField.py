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
  'SearchExpressionField'
]

# Python imports
import copy

# This module imports
import ShotgunORM

class SearchExpressionField(ShotgunORM.SgFieldEntityMulti):
  '''
  An example user field that performs a Shotgun search for its return result.

  Finds all HumanUser Entities that are not named "Bob Smith".
  '''

  def __init__(self, name, label=None, sgEntity=None):
    super(SearchExpressionField, self).__init__(name, label, sgEntity=sgEntity)

    # Don't allow the field to be modified!
    self.schemaInfo().setEditable(False)

    self._searchEntityType = 'HumanUser'

    self._searchFilters = [
      [
        'name',
        'is_not',
        'Bob Smith'
      ]
    ]

    self._searchFields = [
      'firstname',
      'name',
      'lastname',
      'email'
    ]

  def searchFields(self):
    '''
    Returns the fields that will be filled in for matching Entities.
    '''

    return self._searchFields

  def searchFilters(self):
    '''
    Returns the search filters used for the Shotgun search.
    '''

    if self._searchFilters == None:
      return None

    return copy.deepcopy(self._searchFilters)

  def searchEntityType(self):
    '''
    Returns the Entity type that this field searches for.
    '''

    return self._searchEntityType

  def _valueSg(self):
    '''
    Performs the Shotgun search for this field and returns the result.

    The return result of this is the value that the field will return.
    '''

    parent = self.parentEntity()

    print parent

    if parent == None:
      return None

    sgSearch = parent.connection()._sg_find(
      self.searchEntityType(),
      self.searchFilters(),
      self.searchFields()
    )

    return sgSearch
