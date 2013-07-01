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
  'AFTER_ENTITY_COMMIT_CBS',
  'BEFORE_ENTITY_COMMIT_CBS',
  'ON_ENTITY_CREATE_CBS',
  'ON_FIELD_CHANGED_CBS',
  'ON_SCHEMA_CHANGED_CBS',
  'addAfterEntityCommit',
  'addBeforeEntityCommit',
  'addOnEntityCreate',
  'addOnFieldChanged',
  'addOnSchemaChanged',
  'appendAfterEntityCommit',
  'appendBeforeEntityCommit',
  'appendOnEntityCreate',
  'appendOnFieldChanged',
  'appendOnSchemaChanged',
  'afterEntityCommit',
  'beforeEntityCommit',
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

def _defaultAfterEntityCommit(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError):
  ShotgunORM.LoggerCallback.debug('afterEntityCommit: %s' % sgEntity)

def _defaultBeforeEntityCommit(sgEntity, sgBatchData, sgCommitData):
  ShotgunORM.LoggerCallback.debug('beforeEntityCommit: %s' % sgEntity)

def _defaultOnEntityCreate(sgEntity):
  ShotgunORM.LoggerCallback.debug('onEntityCreate: %s' % sgEntity)

def _defaultOnFieldChanged(sgField):
  ShotgunORM.LoggerCallback.debug('onFieldChanged: %s' % sgField)

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

AFTER_ENTITY_COMMIT_CBS = {
  '*': [
    {
      'cb': _defaultAfterEntityCommit,
      'description': 'default_cb'
    }
  ]
}

BEFORE_ENTITY_COMMIT_CBS = {
  '*': [
    {
      'cb': _defaultBeforeEntityCommit,
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
  '*': []
}

def addAfterEntityCommit(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the afterEntityCommit
  callback list.

  This callback will be executed after an Entity is committed to Shotgun.

  Note:
    The callback must contain 5 args.  See the documentation for
    ShotgunORM.afterEntityCommit() for detailed arg information.

    def myCallback(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    AFTER_ENTITY_COMMIT_CBS[filterName].insert(0, data)
  except:
    AFTER_ENTITY_COMMIT_CBS[filterName] = [data]

def appendAfterEntityCommit(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the end of the afterEntityCommit
  callback list.

  This callback will be executed after an Entity is committed to Shotgun.

  Note:
    The callback must contain 5 args.  See the documentation for
    ShotgunORM.afterEntityCommit() for detailed arg information.

    def myCallback(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    AFTER_ENTITY_COMMIT_CBS[filterName].append(data)
  except:
    AFTER_ENTITY_COMMIT_CBS[filterName] = [data]

def addBeforeEntityCommit(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the beforeEntityCommit
  callback list.

  This callback will be executed before an Entity is committed to Shotgun.

  Note:
    The callback must contain 3 args.  See the documentation for
    ShotgunORM.beforeEntityCommit() for detailed arg information.

    def myCallback(sgEntity, sgBatchData, sgCommitData):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    BEFORE_ENTITY_COMMIT_CBS[filterName].insert(0, data)
  except:
    BEFORE_ENTITY_COMMIT_CBS[filterName] = [data]

def appendBeforeEntityCommit(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the end of the beforeEntityCommit
  callback list.

  This callback will be executed before an Entity is committed to Shotgun.

  Note:
    The callback must contain 3 args.  See the documentation for
    ShotgunORM.beforeEntityCommit() for detailed arg information.

    def myCallback(sgEntity, sgBatchData, sgCommitData):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    BEFORE_ENTITY_COMMIT_CBS[filterName].append(data)
  except:
    BEFORE_ENTITY_COMMIT_CBS[filterName] = [data]

def addOnEntityCreate(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the onEntityCreate callback
  list.

  This callback will be executed anytime an Entity object is created.

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onEntityCreate() for detailed arg information.

    def myCallback(sgEntity):
      ...
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

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onEntityCreate() for detailed arg information.

    def myCallback(sgEntity):
      ...
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

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onFieldChanged() for detailed arg information.

    def myCallback(sgField):
      ...
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

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onFieldChanged() for detailed arg information.

    def myCallback(sgField):
      ...
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

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onSchemaChanged() for detailed arg information.

    def myCallback(sgSchema):
      ...
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

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onSchemaChanged() for detailed arg information.

    def myCallback(sgSchema):
      ...
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

def afterEntityCommit(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError):
  '''
  This function is called after an Entity has been committed to Shotgun.

  Args:
    * (SgEntity) sgEntity:
      Entity that is committing.

    * (dict) sgBatchData:
      Shotgun formatted batch dictionary of the Entities commit data.

    * (list) sgBatchResult:
      Result returned from Shotgun for the commit.

    * (dict) sgCommitData:
      Dictionary used to pass data user between beforeCommit() and
      afterCommit().

    * (Exception) sgCommitError:
      Exception raised anytime during the commit process.  When this is not None
      perform cleanup operations because the commit failed.
  '''

  entityType = sgEntity.type

  if AFTER_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = AFTER_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError)

  cbs = AFTER_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgCommitError)

def beforeEntityCommit(sgEntity, sgBatchData, sgCommitData):
  '''
  This function is called before an Entity has been committed to Shotgun.

  Args:
    * (SgEntity) sgEntity:
      Entity that is committing.

    * (dict) sgBatchData:
      Shotgun formatted batch dictionary of the Entities commit data.

    * (dict) sgCommitData:
      Dictionary used to pass data user between beforeCommit() and
      afterCommit().
  '''

  entityType = sgEntity.type

  if BEFORE_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = BEFORE_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgCommitType, sgCommitData)

  cbs = BEFORE_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgBatchData, sgCommitData)

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

def onFieldChanged(sgField):
  '''
  This function is called anytime an Entity fields value changes.

  Called during:
    1: When a field validates itself.
    2: When a field is set to a new value.
    3: When a field is set to cache data.
    4: When a fields SgField.changed() function is called.
  '''

  entityFieldName = sgField.parentEntity().type + '.' + sgField.name()

  if ON_FIELD_CHANGED_CBS.has_key(entityFieldName):
    cbs = ON_FIELD_CHANGED_CBS[entityFieldName]

    for i in cbs:
      i['cb'](sgField)

  entityFieldName = sgField.name()

  if ON_FIELD_CHANGED_CBS.has_key(entityFieldName):
    cbs = ON_FIELD_CHANGED_CBS[entityFieldName]

    for i in cbs:
      i['cb'](sgField)

  cbs = ON_FIELD_CHANGED_CBS['*']

  for i in cbs:
    i['cb'](sgField)

def onSchemaChanged(sgSchema):
  '''
  Called whenever a SgSchema initializes or rebuilds.
  '''

  url = sgSchema.url()

  _defaultOnSchemaChanged(sgSchema)

  if ON_SCHEMA_CHANGED_CBS.has_key(url):
    cbs = ON_SCHEMA_CHANGED_CBS[url]

    for i in cbs:
      i['cb'](sgSchema)

  cbs = ON_SCHEMA_CHANGED_CBS['*']

  for i in cbs:
    i['cb'](sgSchema)
