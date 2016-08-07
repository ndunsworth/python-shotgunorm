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
  'AFTER_ENTITY_COMMIT_CBS',
  'BEFORE_ENTITY_COMMIT_CBS',
  'BEFORE_ENTITY_CREATE_CBS',
  'ON_ENTITY_CREATE_CBS',
  'ON_ENTITY_SCHEMA_INFO_CREATE_CBS',
  'ON_FIELD_CHANGED_CBS',
  'ON_SCHEMA_CHANGED_CBS',
  'ON_SEARCH_RESULT_CBS',
  'addAfterEntityCommit',
  'addBeforeEntityCommit',
  'addOnEntityCreate',
  'addOnEntitySchemaInfoCreate',
  'addOnFieldChanged',
  'addOnSchemaChanged',
  'addOnSearchResult',
  'appendAfterEntityCommit',
  'appendBeforeEntityCommit',
  'appendOnEntityCreate',
  'appendOnEntitySchemaInfoCreate',
  'appendOnFieldChanged',
  'appendOnSchemaChanged',
  'appendOnSearchResult',
  'afterEntityCommit',
  'beforeEntityCommit',
  'beforeEntityCreate',
  'onEntityCreate',
  'onEntitySchemaInfoCreate',
  'onFieldChanged',
  'onSchemaChanged',
  'onSearchResult'
]

# Python imports
import os
import socket

# This module imports
import ShotgunORM

def _defaultAfterEntityCommit(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError):
  ShotgunORM.LoggerCallback.debug('afterEntityCommit: %s' % sgEntity)

def _defaultBeforeEntityCommit(sgEntity, sgBatchData, sgCommitData, sgDryRun):
  ShotgunORM.LoggerCallback.debug('beforeEntityCommit: %s' % sgEntity)

def _defaultBeforeEntityCreate(sgConnection, sgEntityType, sgData):
  if sgEntityType == 'ApiUser' or sgEntityType == 'PermissionRuleSet':
    try:
      del sgData['name']

      ShotgunORM.LoggerCallback.debug(
        'beforeEntityCreate: %(entityType)s removing "name" field data' % {
          'entityType': sgEntityType
        }
      )
    except:
      pass

  return sgData

def _defaultOnEntityCreate(sgEntity):
  ShotgunORM.LoggerCallback.debug('onEntityCreate: %s' % sgEntity)

def _defaultOnEntitySchemaInfoCreate(sgEntitySchemaInfo):
  fieldInfoData = ShotgunORM.SgFieldSchemaInfo.createSchemaData(
    sgEntitySchemaInfo.name(),
    'type',
    ShotgunORM.SgField.RETURN_TYPE_TEXT,
    editable=False,
    label='Type'
  )

  fieldInfoData['commitable'] = False
  fieldInfoData['queryable'] = False

  fieldInfo = ShotgunORM.SgFieldSchemaInfo(fieldInfoData)

  sgEntitySchemaInfo._fieldInfos['type'] = fieldInfo

def _defaultOnEntitySchemaInfoCreatePhaseTask(sgEntitySchemaInfo):
  colorField = sgEntitySchemaInfo.fieldInfo('color')

  colorField._returnType = ShotgunORM.SgField.RETURN_TYPE_COLOR2

def _defaultOnFieldChanged(sgField):
  ShotgunORM.LoggerCallback.debug('onFieldChanged: %s' % sgField)

def _defaultOnSchemaChanged(sgSchema):
  ShotgunORM.LoggerCallback.debug('onSchemaChanged: %s' % sgSchema)

  url = sgSchema.url()

  connections = ShotgunORM.SgConnection.__metaclass__.connections(url)

  for connection in connections:
    connection.schemaChanged()

def _defaultOnSearchResult(sgConnection, sgEntityType, sgFields, sgResults):
  pass

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

BEFORE_ENTITY_CREATE_CBS = {
  '*': [
    {
      'cb': _defaultBeforeEntityCreate,
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

ON_ENTITY_SCHEMA_INFO_CREATE_CBS = {
  '*': [
    {
      'cb': _defaultOnEntitySchemaInfoCreate,
      'description': 'adds the type field to all Entity classes'
    }
  ],
  'Phase': [
    {
      'cb': _defaultOnEntitySchemaInfoCreatePhaseTask,
      'description': 'changes color field return type to color2'
    }
  ],
  'Task': [
    {
      'cb': _defaultOnEntitySchemaInfoCreatePhaseTask,
      'description': 'changes color field return type to color2'
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

ON_SEARCH_RESULT_CBS = {
  '*': [
    {
      'cb': _defaultOnSearchResult,
      'description': 'default_cb'
    }
  ]
}

def addAfterEntityCommit(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the afterEntityCommit
  callback list.

  This callback will be executed after an Entity is committed to Shotgun.

  Note:
    The callback must contain 5 args.  See the documentation for
    ShotgunORM.afterEntityCommit() for detailed arg information.

    def myCallback(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError):
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

    def myCallback(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError):
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

    def myCallback(sgEntity, sgBatchData, sgCommitData, sgDryRun):
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

    def myCallback(sgEntity, sgBatchData, sgCommitData, sgDryRun):
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

def addBeforeEntityCreate(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the beforeEntityCreate
  callback list.

  This callback will be executed before an Entity object is created.
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    BEFORE_ENTITY_CREATE_CBS[filterName].insert(0, data)
  except:
    BEFORE_ENTITY_CREATE_CBS[filterName] = [data]

def appendBeforeEntityCreate(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the end of the beforeEntityCreate
  callback list.

  This callback will be executed before an Entity object is created.
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    BEFORE_ENTITY_CREATE_CBS[filterName].append(data)
  except:
    BEFORE_ENTITY_CREATE_CBS[filterName] = [data]

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

def addOnEntitySchemaInfoCreate(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the front of the onEntityInfoCreate
  callback list.

  This callback will be executed anytime an Entity info object is created.

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onEntityInforeate() for detailed arg information.

    def myCallback(sgEntityInfo):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_SCHEMA_INFO_CREATE_CBS[filterName].insert(0, data)
  except:
    ON_ENTITY_SCHEMA_INFO_CREATE_CBS[filterName] = [data]

def appendOnEntitySchemaInfoCreate(cb, filterName='*', description=''):
  '''
  Adds the callback and places it at the end of the onEntityInfoCreate
  callback list.

  This callback will be executed anytime an Entity info object is created.

  Note:
    The callback must contain 1 args.  See the documentation for
    ShotgunORM.onEntityInfoCreate() for detailed arg information.

    def myCallback(sgEntityInfo):
      ...
  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_ENTITY_SCHEMA_INFO_CREATE_CBS[filterName].append(data)
  except:
    ON_ENTITY_SCHEMA_INFO_CREATE_CBS[filterName] = [data]

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

def addOnSearchResult(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_SEARCH_RESULT_CBS[filterName].insert(0, data)
  except:
    ON_SEARCH_RESULT_CBS[filterName] = [data]

def appendOnSearchResult(cb, filterName='*', description=''):
  '''

  '''

  if filterName in [None, '']:
    filterName = '*'

  data = {
    'cb': cb,
    'description': description
  }

  try:
    ON_SEARCH_RESULT_CBS[filterName].append(data)
  except:
    ON_SEARCH_RESULT_CBS[filterName] = [data]

def afterEntityCommit(sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError):
  '''
  This function is called after an Entity has been committed to Shotgun.

  Args:
    * (SgEntity) sgEntity:
      Entity that is committing.

    * (dict) sgBatchData:
      List of Shotgun formatted batch commit data.

    * (list) sgBatchResult:
      Result returned from Shotgun for the commit.

    * (dict) sgCommitData:
      Dictionary used to pass user data between beforeCommit() and
      afterCommit().

    * (bool) sgDryRun:
      When True the commit is not updating Shotgun with any modifications,
      it is only in a test phase.

    * (Exception) sgCommitError:
      Exception raised anytime during the commit process.  When this is not None
      perform cleanup operations because the commit failed.
  '''

  entityType = sgEntity.type

  if AFTER_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = AFTER_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError)

  cbs = AFTER_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgBatchData, sgBatchResult, sgCommitData, sgDryRun, sgCommitError)

def beforeEntityCommit(sgEntity, sgBatchData, sgCommitData, sgDryRun):
  '''
  This function is called before an Entity has been committed to Shotgun.

  Args:
    * (SgEntity) sgEntity:
      Entity that is committing.

    * (list) sgBatchData:
      List of Shotgun formatted batch commit data.

    * (dict) sgCommitData:
      Dictionary used to pass user data between beforeCommit() and
      afterCommit().

    * (bool) sgDryRun:
      When True the commit is not updating Shotgun with any modifications,
      it is only in a test phase.
  '''

  entityType = sgEntity.type

  if BEFORE_ENTITY_COMMIT_CBS.has_key(entityType):
    cbs = BEFORE_ENTITY_COMMIT_CBS[entityType]

    for i in cbs:
      i['cb'](sgEntity, sgCommitType, sgCommitData, sgDryRun)

  cbs = BEFORE_ENTITY_COMMIT_CBS['*']

  for i in cbs:
    i['cb'](sgEntity, sgBatchData, sgCommitData, sgDryRun)

def beforeEntityCreate(sgConnection, sgEntityType, sgData):
  '''
  This function called before an SgEntity object is created.

  The Shotgun connection, entity type, and Shotgun data that will be used to
  initialize the SgEntity are passed to each callback.
  '''

  cbs = BEFORE_ENTITY_CREATE_CBS.get(sgEntityType, [])

  for i in cbs:
    try:
      updated = i['cb'](sgConnection, sgEntityType, sgData)

      if isinstance(updated, list):
        sgData = updated
    except Exception, e:
      print e

  cbs = BEFORE_ENTITY_CREATE_CBS['*']

  for i in cbs:
    try:
      updated = i['cb'](sgConnection, sgEntityType, sgData)

      if isinstance(updated, list):
        sgData = updated
    except Exception, e:
      print e

  return sgData

def onEntityCreate(sgEntity):
  '''
  This function is called anytime an Entity object is created.  Not to be
  confused with when an Entity is created in the Shotgun database.
  '''

  entityType = sgEntity.type

  if ON_ENTITY_CREATE_CBS.has_key(entityType):
    cbs = ON_ENTITY_CREATE_CBS[entityType]

    for i in cbs:
      try:
        i['cb'](sgEntity)
      except Exception, e:
        print e

  if sgEntity.isCustom():
    if ON_ENTITY_CREATE_CBS.has_key(sgEntity.label()):
      cbs = ON_ENTITY_CREATE_CBS[sgEntity.label()]

      for i in cbs:
        try:
          i['cb'](sgEntity)
        except Exception, e:
          print e

  cbs = ON_ENTITY_CREATE_CBS['*']

  for i in cbs:
    try:
      i['cb'](sgEntity)
    except Exception, e:
      print e

def onEntitySchemaInfoCreate(sgEntityInfo):
  '''
  This function is called anytime an Entity info object is created.
  '''

  entityType = sgEntityInfo.name()

  if ON_ENTITY_SCHEMA_INFO_CREATE_CBS.has_key(entityType):
    cbs = ON_ENTITY_SCHEMA_INFO_CREATE_CBS[entityType]

    for i in cbs:
      try:
        i['cb'](sgEntityInfo)
      except Exception, e:
        print e

  if sgEntityInfo.isCustom():
    if ON_ENTITY_SCHEMA_INFO_CREATE_CBS.has_key(sgEntityInfo.label()):
      cbs = ON_ENTITY_SCHEMA_INFO_CREATE_CBS[sgEntityInfo.label()]

      for i in cbs:
        try:
          i['cb'](sgEntityInfo)
        except Exception, e:
          print e

  cbs = ON_ENTITY_SCHEMA_INFO_CREATE_CBS['*']

  for i in cbs:
    try:
      i['cb'](sgEntityInfo)
    except Exception, e:
      print e

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
      try:
        i['cb'](sgField)
      except Exception, e:
        print e

  entityFieldName = sgField.name()

  if ON_FIELD_CHANGED_CBS.has_key(entityFieldName):
    cbs = ON_FIELD_CHANGED_CBS[entityFieldName]

    for i in cbs:
      try:
        i['cb'](sgField)
      except Exception, e:
        print e

  cbs = ON_FIELD_CHANGED_CBS['*']

  for i in cbs:
    try:
      i['cb'](sgField)
    except Exception, e:
      print e

def onSchemaChanged(sgSchema):
  '''
  Called whenever a SgSchema initializes or rebuilds.
  '''

  url = sgSchema.url()

  _defaultOnSchemaChanged(sgSchema)

  if ON_SCHEMA_CHANGED_CBS.has_key(url):
    cbs = ON_SCHEMA_CHANGED_CBS[url]

    for i in cbs:
      try:
        i['cb'](sgSchema)
      except Exception, e:
        print e

  cbs = ON_SCHEMA_CHANGED_CBS['*']

  for i in cbs:
    try:
      i['cb'](sgSchema)
    except Exception, e:
      print e

def onSearchResult(sgConnection, sgEntityType, sgFields, sgResults):
  '''
  Called whenever a Shotgun search is performed.
  '''

  cbs = ON_SEARCH_RESULT_CBS.get(sgEntityType, [])

  for i in cbs:
    try:
      updated = i['cb'](sgConnection, sgEntityType, list(sgFields), sgResults)

      if isinstance(updated, list):
        sgResults = updated
    except Exception, e:
      print e

  cbs = ON_SEARCH_RESULT_CBS['*']

  for i in cbs:
    try:
      updated = i['cb'](sgConnection, sgEntityType, list(sgFields), sgResults)

      if isinstance(updated, list):
        sgResults = updated
    except Exception, e:
      print e

  return sgResults
