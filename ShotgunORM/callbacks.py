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
  'COMMIT_TYPE_NONE',
  'COMMIT_TYPE_CREATE',
  'COMMIT_TYPE_DELETE',
  'COMMIT_TYPE_REVIVE',
  'COMMIT_TYPE_UPDATE',
  'ON_ENTITY_COMMIT_CBS',
  'ON_ENTITY_CREATE_CBS',
  'ON_FIELD_CHANGED_CBS',
  'ON_SCHEMA_CHANGED_CBS',
  'addOnEntityCommit',
  'addOnEntityCreate',
  'addOnFieldChanged',
  'addOnSchemaChanged',
  'appendOnEntityCommit',
  'appendOnEntityCreate',
  'appendOnFieldChanged',
  'appendOnSchemaChanged',
  'onEntityCommit',
  'onEntityCreate',
  'onFieldChanged',
  'onSchemaChanged'
]

# Python imports
import os
import socket

# This module imports
import ShotgunORM

COMMIT_TYPE_NONE = 0
COMMIT_TYPE_CREATE = 1
COMMIT_TYPE_DELETE = 2
COMMIT_TYPE_REVIVE = 3
COMMIT_TYPE_UPDATE = 4

def _defaultOnEntityCommit(sgEntity, sgCommitType):
  ShotgunORM.LoggerCallback.debug('onEntityCommit: %s %d' % (sgEntity, sgCommitType))

def _defaultOnEntityCreate(sgEntity):
  ShotgunORM.LoggerCallback.debug('onEntityCreate: %s' % sgEntity)

def _defaultOnFieldChanged(sgEntityField):
  ShotgunORM.LoggerCallback.debug('onFieldChanged: %s' % sgEntityField)

def _defaultOnSchemaChanged(sgSchema):
  ShotgunORM.LoggerCallback.debug('onSchemaChanged: %s' % sgSchema)

  url = sgSchema.url()

  connections = ShotgunORM.SgConnection.__metaclass__.connections(url)

  for connection in connections:
    connection.schemaChanged()

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
      'cb': _defaultOnFieldChanged,
      'description': 'default_cb'
    }
  ]
}

ON_SCHEMA_CHANGED_CBS = {
  '*': [
    {
      'cb': _defaultOnSchemaChanged,
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
  Adds the callback and places it at the front of the onEntityCreate callback
  list.

  This callback will be executed anytime an Entity object is created.
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
  Adds the callback and places it at the end of the onEntityCreate callback
  list.

  This callback will be executed anytime an Entity object is created.
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
  Adds the callback and places it at the front of the onFieldChanged callback
  list.

  This callback will be executed anytime an Entity objects field is modified.
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
  Adds the callback and places it at the end of the onFieldChanged callback
  list.

  This callback will be executed anytime an Entity objects field is modified.
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

def addOnSchemaChanged(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the onSchemaChanged callback
  list.

  This callback will be executed anytime a schema object initializes or rebuilds.
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_SCHEMA_CHANGED_CBS[filterName].insert(0, data)
  except:
    ON_SCHEMA_CHANGED_CBS[filterName] = [data]

def appendOnSchemaChanged(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the end of the onSchemaChanged callback
  list.

  This callback will be executed anytime a schema object initializes or rebuilds.
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_SCHEMA_CHANGED_CBS[filterName].append(data)
  except:
    ON_SCHEMA_CHANGED_CBS[filterName] = [data]

def onEntityCommit(sgEntity, sgBatchData):
  '''

  '''

  entityType = sgEntity.type

  if ON_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = ON_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgCommitType)

  cbs = ON_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgBatchData)

def onEntityCreate(sgEntity):
  '''
  This function is called anytime an Entity object is created.  Not to be
  confused with when an Entity is created in the Shotgun database.
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
  This function is called anytime an Entity fields value changes.

  Called during:
    1: When a field validates itself.
    2: When a field is set to a new value.
    3: When a field is set to cache data.
    4: When a fields SgField.changed() function is called.
  '''

  entityFieldName = sgEntityField.parentEntity().type + '.' + sgEntityField.name()

  if ON_FIELD_CHANGED_CBS.has_key(entityFieldName):
    cbs = ON_FIELD_CHANGED_CBS[entityFieldName]

    for i in cbs:
      i['cb'](sgEntityField)

  cbs = ON_FIELD_CHANGED_CBS['*']

  for i in cbs:
    i['cb'](sgEntityField)

def onSchemaChanged(sgSchema):
  '''
  Called whenever a SgSchema initializes or rebuilds.
  '''

  url = sgSchema.url()

  if ON_SCHEMA_CHANGED_CBS.has_key(url):
    cbs = ON_SCHEMA_CHANGED_CBS[url]

    for i in cbs:
      i['cb'](sgSchema)

  cbs = ON_SCHEMA_CHANGED_CBS['*']

  for i in cbs:
    i['cb'](sgSchema)
