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
  'SgProject'
]

# This module imports
import ShotgunORM

class SgProject(ShotgunORM.SgEntity):
  '''
  Class that represents a Project Entity.
  '''

  def sequence(self, sequence, sgFields=None):
    '''
    Returns the sequence Entity for this project.

    Args:
      * (str) sequence:
        Name of the sequence.

      * (list) sgFields:
        List of fields to populate the result with.
    '''

    if not self.exists():
      return None

    return self.connection().findOne(
      'Sequence',
      [
        [
          'project',
          'is',
          self
        ],
        [
          'code',
          'name_is',
          sequence
        ]
      ],
      sgFields
    )

  def sequenceNames(self):
    '''
    Returns a list of all Sequence names for this project.
    '''

    result = []

    if not self.exists():
      return result

    seqs = self.sequences(sgFields=['code'])

    for seq in seqs:
      result.append(seq['code'])

    result.sort()

    return result

  def sequences(self, sgFields=None):
    '''
    Returns a list of all Sequence Entities for this project.

      * (list) sgFields:
        List of fields to populate the results with.
    '''

    if not self.exists():
      return []

    return self.connection().find(
      'Sequence',
      [
        [
          'project',
          'is',
          self
        ]
      ],
      sgFields
    )

  def shot(self, sequence, shot, sgFields=None):
    '''
    Returns the Shot Entity for the sequence of this project.

    Args:
      * (str) sequence:
        Name of the sequence the shot belongs to.

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
          'project',
          'is',
          {'type': 'Project', 'id': 64}
        ],
        [
          'sg_sequence',
          'name_is',
          sequence
        ],
        [
          'code',
          'is',
          shot
        ]
      ],
      sgFields
    )

  def shotNames(self, sgSequences=None):
    '''
    Returns a dict containing of all Shot names for this project.

    Args:
      * (list) sgSequences:
        Return only the Shot names associated with the list of Sequences.
    '''

    result = {}

    if not self.exists():
      return result

    seqShots = self.shots(sgFields=['code'])

    for seq, shots in seqShots.items():
      shotNames = []

      for shot in shots:
        shotNames.append(shot['code'])

      result[seq] = shotNames

    return result

  def shots(self, sgSequences=None, sgFields=None):
    '''
    Returns a dict of all Shot Entities for this project.

    Args:
      * (list) sgSequences:
        Return only the Shots associated with the list of Sequences.

      * (list) sgFields:
        List of fields to populate the results with.
    '''

    result = {}

    if not self.exists():
      return result

    if isinstance(sgSequences, (str, ShotgunORM.SgEntity)):
      sgSequences = [sgSequences]

    if sgSequences == None:
      sgSequences = self.sequenceNames()

    if len(sgSequences) <= 0:
      return result

    seqNames = []

    for seq in sgSequences:
      if isinstance(seq, str):
        seqNames.append(seq)
      else:
        seqNames.append(seq['code'])

    qEngine = self.connection().queryEngine()

    # Block the query engine so all Shot fields get pulled at once.
    qEngine.block()

    try:
      sequences = self.connection().find(
        'Sequence',
        [
          [
            'project',
            'is',
            self
          ],
          [
            'code',
            'in',
            seqNames
          ]
        ],
        ['shots']
      )

      for seq in sequences:
        seqField = seq.field('shots')

        result[seq['code']] = seqField.value(sgSyncFields={'Shot': sgFields})
    finally:
      qEngine.unblock()

    return result

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgProject,
  sgEntityTypes=['Project']
)
