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
  'SgSequence'
]

# This module imports
import ShotgunORM

class SgSequence(ShotgunORM.SgEntity):
  '''
  Class that represents a Sequence Entity.
  '''

  def shot(self, shot, sgFields=None):
    '''
    Returns the Shot Entity of this sequence.

    Args:
      * (str) shot:
        Name of the shot.

      * (list) sgFields:
        List of fields to populate the result with.
    '''

    if not self.exists():
      return None

    return self.connection().findOne(
      'Shot',
      [
        [
          'sg_sequence',
          'is',
          self
        ],
        [
          'code',
          'is',
          shot
        ]
      ],
      sgFields
    )

  def shotNames(self):
    '''
    Returns a list containing of all Shot names for this sequence.
    '''

    result = []

    if not self.exists():
      return result

    for shot in self['shots']:
      result.append(shot['code'])

    return result

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgSequence,
  sgEntityTypes=['Sequence']
)
