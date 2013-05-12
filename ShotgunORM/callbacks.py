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
  'COMMIT_TYPE_CREATE',
  'COMMIT_TYPE_DELETE',
  'COMMIT_TYPE_REVIVE',
  'COMMIT_TYPE_UPDATE',
  'ON_ENTITY_COMMIT_CBS',
  'ON_ENTITY_CREATE_CBS',
  'ON_FIELD_CHANGED_CBS',
  'addOnEntityCommit',
  'addOnEntityCreate',
  'addOnFieldChanged',
  'appendOnEntityCommit',
  'appendOnEntityCreate',
  'appendOnFieldChanged',
  'onEntityCommit',
  'onEntityCreate',
  'onFieldChanged'
]

# Python imports
import os
import socket

# This module imports
from ShotgunORM import LoggerCallback

COMMIT_TYPE_CREATE = 0
COMMIT_TYPE_DELETE = 1
COMMIT_TYPE_REVIVE = 2
COMMIT_TYPE_UPDATE = 3

def _defaultOnEntityCommit(sgEntity, sgCommitType):
  LoggerCallback.debug('onEntityCommit: %s %d' % (sgEntity.__repr__(), sgCommitType))

def _defaultOnEntityCreate(sgEntity):
  LoggerCallback.debug('onEntityCreate: %s' % sgEntity.__repr__())

def _defaultOnFieldChangedCb(sgEntityField):
  LoggerCallback.debug('onFieldChanged: %s' % sgEntityField.__repr__())

#def _defaultOnFieldChangedCb(sgEntityField):
#  soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#  soc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#
#  parent = sgEntityField.parentEntity()
#
#  msg = '%s %s %s %d %s' % (
#    '%s@%s' % (
#      os.getenv('USERNAME', 'unknown'),
#      socket.gethostname()
#    ),
#    parent.session().connection().url(),
#    parent.type,
#    parent.id,
#    sgEntityField.name()
#  )
#
#  soc.sendto(msg, ('<broadcast>', 7479))
#
#  soc.close()

ON_ENTITY_COMMIT_CBS = {
  '*': [
    {
      'cb': _defaultOnEntityCommit,
      'description': 'default_cb'
    }
  ]
}

ON_ENTITY_CREATE_CBS = {
  '*': [
    {
      'cb': _defaultOnEntityCreate,
      'description': 'default_cb'
    }
  ]
}

ON_FIELD_CHANGED_CBS = {
  '*': [
    {
      'cb': _defaultOnFieldChangedCb,
      'description': 'default_cb'
    }
  ]
}

def addOnEntityCommit(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_COMMIT_CBS[filterName].insert(0, data)
  except:
    ON_ENTITY_COMMIT_CBS[filterName] = [data]

def appendOnEntityCommit(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_COMMIT_CBS[filterName].append(data)
  except:
    ON_ENTITY_COMMIT_CBS[filterName] = [data]

def addOnEntityCreate(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_CREATE_CBS[filterName].insert(0, data)
  except:
    ON_ENTITY_CREATE_CBS[filterName] = [data]

def appendOnEntityCreate(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_CREATE_CBS[filterName].append(data)
  except:
    ON_ENTITY_CREATE_CBS[filterName] = [data]

def addOnFieldChanged(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_FIELD_CHANGED_CBS[filterName].insert(0, data)
  except:
    ON_FIELD_CHANGED_CBS[filterName] = [data]

def appendOnFieldChanged(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_FIELD_CHANGED_CBS[filterName].append(data)
  except:
    ON_FIELD_CHANGED_CBS[filterName] = [data]

def onEntityCommit(sgEntity, sgCommitType):
  '''

  '''

  entityType = sgEntity.type

  if ON_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = ON_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgCommitType)

  cbs = ON_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgCommitType)

def onEntityCreate(sgEntity):
  '''

  '''

  entityType = sgEntity.type

  if ON_ENTITY_CREATE_CBS.has_key(entityType):
    cbs = ON_ENTITY_CREATE_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity)

  cbs = ON_ENTITY_CREATE_CBS['*']

  for i in cbs:
    i['cb'](sgEntity)

def onFieldChanged(sgEntityField):
  '''

  '''

  entityFieldName = sgEntityField.parentEntity().type + '.' + sgEntityField.name()

  if ON_FIELD_CHANGED_CBS.has_key(entityFieldName):
    cbs = ON_FIELD_CHANGED_CBS[entityFieldName]

    for i in cbs:
      i['cb'](sgEntityField)

  cbs = ON_FIELD_CHANGED_CBS['*']

  for i in cbs:
    i['cb'](sgEntityField)
