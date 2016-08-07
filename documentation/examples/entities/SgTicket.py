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
  'SgTicket'
]

# This module imports
import ShotgunORM

class SgTicket(ShotgunORM.SgEntity):
  '''
  Class that represents a Ticket Entity.
  '''

  def reply(self, sgMsg, sgUser=None, sgCommit=False):
    '''
    Creates a reply to the ticket.

    When the arg "sgUser", valid value types (SgApiUser, SgHumanUser or str), is
    specified the ticket will be a reply from that user.

    Returns the Reply Entity.

    Note:
    If the arg "sgCommit" is False then the returned Reply Entity has not yet
    been published to Shotgun.  You must call commit() on the returned Entity.

    Args:
      * (str) sgMsg:
        Reply message.

      * (HumanUser, str) sgUser:
        User which the replay will originate from.  If left as None then the
        connections SgApiUser will be used.

      * (bool) sgCommit:
        Commit the reply immediately.
    '''

    if not self.exists():
      raise RuntimError('unable to reply to ticket, does not exist in Shotgun')

    connection = self.connection()

    replyData = None

    if sgUser != None:
      if isinstance(sgUser, str):
        user = connection.findOne('HumanUser', [['name', 'is', sgUser]])

        if user == None:
          raise RuntimeError('unable to find HumanUser "%s"' % sgUser)

        sgUser = user
      elif not isinstance(sgUser, (SgApiUser, SgHumanUser)):
        raise TypeError('expected a ApiUser/HumanUser Entity or a user name, got %s' % sgUser.__class__.__name__)

      replyData = {
        'content': sgMsg,
        'entity': self.toEntityFieldData(),
        'user': sgUser.toEntityFieldData()
      }
    else:
      replyData = {
        'content': sgMsg,
        'entity': self.toEntityFieldData(),
      }

    result = connection.create('Reply', replyData, sgCommit=sgCommit)

    return result

  def close(self, sgMsg, sgUser=None, sgCommit=False):
    '''
    Sets the tickets status to closed and creates a reply.

    Returns the reply Entity.

    Args:
      * (str) sgMsg:
        Reply message.

      * (HumanUser, str) sgUser:
        User which the replay will originate from.  If left as None then the
        connections SgApiUser will be used.

      * (bool) sgCommit:
        Commit the reply immediately.
    '''

    with self:
      if not self.exists():
        raise RuntimError('unable to close ticket, does not exist in Shotgun')

      if not isinstance(sgMsg, str):
        raise TypeError('expected a str for "sgMsg" got %s' % sgMsg)

      if sgUser != None:
        if isinstance(sgUser, str):
          user = sg.searchOne('HumanUser', 'name == "%s"' % sgUser)

          if user == None:
            raise RuntimeError('not able to find Shotgun user "%s"' % sgUser)

          sgUser = user
        elif isinstance(sgUser, SgEntity):
          if not sgUser.type == 'HumanUser':
            raise TypeError('invalid entity type "%s" expected a HumanUser' % sgUser.type)

      fieldStatus = self.field('sg_status_list')

      fieldStatus.setValue('res')

      connection = self.connection()

      replyEntity = connection.create('Reply', {
        'content': sgMsg,
        'entity': self.toEntityFieldData()
      })

      if sgUser != None:
        replyEntity['user'] = sgUser

      if not sgCommit:
        return replyEntity

      batchData = []

      if fieldStatus.hasCommit():
        batchData.append(
          {
            'entity': self,
            'batch_data': self.toBatchData(['sg_status_list'])
          }
        )

      batchData.append(
        {
          'entity': replyEntity,
          'batch_data': replyEntity.toBatchData()
        }
      )

      connection._batch(batchData)

      return replyEntity

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgTicket,
  sgEntityTypes=['Ticket']
)
