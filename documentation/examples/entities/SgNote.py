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
  'SgNote'
]

# This module imports
import ShotgunORM

class SgNote(ShotgunORM.SgEntity):
  '''
  Class that represents a Note Entity.
  '''

  def conversation(self, sgEntityFields=None):
    '''
    Returns the full conversation of the Note.

    This will include the Note entity followed by Replay and/or Attachment
    Entities.

    Args:
      * (dict) sgEntityFields:
        Dict that may contain the following keys, Attachment, Note, Reply.
        Each keys value should be a list of field names to populate for each
        Entity type.

        Additional keys are ignored.
    '''

    if self.exists() == False:
      return []

    connection = self.connection()

    fillFields = {
      'Attachment': list(connection.defaultEntityQueryFields('Attachment')),
      'Note': list(connection.defaultEntityQueryFields('Note')),
      'Reply': list(connection.defaultEntityQueryFields('Reply'))
    }

    if sgEntityFields != None:
      fillFields['Attachment'].extend(sgEntityFields.get('Attachment', []))
      fillFields['Note'].extend(sgEntityFields.get('Note', []))
      fillFields['Reply'].extend(sgEntityFields.get('Reply', []))

    data = connection.connection().note_thread_read(
      self.field('id').value(),
      fillFields
    )

    result = []

    for i in data:
      result.append(
        connection._createEntity(i['type'], i, None)
      )

    return result

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgNote,
  sgEntityTypes=['Note']
)
