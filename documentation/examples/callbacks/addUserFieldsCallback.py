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
  'addUserFieldsCallback'
]

# This module imports
import ShotgunORM

################################################################################
#
# The custom field that will be added to all ApiUser Entity objects.
#
################################################################################

class ApiUserNameField(ShotgunORM.SgFieldText):
  '''
  Field that returns the value of the "firstname" and "lastname".
  '''

  def __init__(self):
    super(ApiUserNameField, self).__init__('name')

    # Don't allow the field to be modified!
    self.schemaInfo().setEditable(False)

  def _valueSg(self):
    parent = self.parentEntity()

    if parent == None:
      return None

    values = parent.fieldValues(['firstname', 'lastname'])

    return '%(firstname)s %(lastname)s' % values

################################################################################
#
# The callback that will be registered to onEntityCreate() and will add the
# name field to ApiUser Entity objects.
#
################################################################################

def addApiUserNameField(sgEntity):
  '''
  This example callback shows how to add user fields to Entity objects as they
  are created.

  A SgUserField will be created for all ApiUser Entity objects that adds a name
  field for the Entity.  ApiUsers do not contain a "name" field as part of the
  Shotgun schema.
  '''

  if sgEntity.type == 'ApiUser':
    if not sgEntity.hasField('name'):
      sgEntity.addField(ApiUserNameField())

################################################################################
#
# Register the callback with ShotgunORM onEntityCreate().
#
################################################################################

ShotgunORM.addOnEntityCreate(
  addApiUserNameField,
  filterName='ApiUser',
  description='callback that adds a name field to ApiUser Entity objects'
)
