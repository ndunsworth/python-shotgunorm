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

################################################################################
# This sub-module is loaded at the end of the ShotgunORM __init__.py.
#
# You can customize the ShotgunORM library through this module.
#
# WARNING!
# It is advised you put your customizations at the end of this file in the
# section designated for them.  Future versions of the library may modify this
# file so its best to keep your modifications grouped so you can differentiate
# between your modifications and updates to the library.
#
# Happy hacking!
################################################################################

__all__ = [
  'DEFAULT_CONNECTION_CACHING',
  'DISABLE_FIELD_VALIDATE_ON_SET_VALUE',
  'ENABLE_FIELD_QUERY_PROFILING',
  'ENTITY_DIR_INCLUDE_FIELDS',
  'SHOTGUNAPI_NAME'
]

# Python imports
import os

# This module imports
import ShotgunORM

################################################################################
#
# Name of the Shotgun API library.
#
# This is the name that the ShotgunORM will use to import the Python API
# provided by Shotgun Software.
#
################################################################################

SHOTGUNAPI_NAME = os.getenv('PY_SHOTGUNAPI_NAME', 'shotgun_api3')

################################################################################
#
# Controls the default value that connections use for enabling/disabling Entity
# caching.
#
# Setting this value to False will make all SgConnection objects disable Entity
# caching.  Changing this config value will only affect new SgConnection objects
# and not pre-existing ones.
#
################################################################################

DEFAULT_CONNECTION_CACHING = bool(
  os.getenv('PY_SGORM_DEFAULT_CONNECTION_CACHING', True)
)

################################################################################
#
# Disables the action of fields validating when being set to a new value.
#
# Fields validate before being set to a new value, this means if the field has
# not pulled its value from Shotgun then a db query will be run.  The main point
# of this is for fields to not be flagged as having an update when the new value
# is already the current Shotgun database value.
#
# If you wish to never check the new value against the database then set this
# config variable to True.
#
################################################################################

DISABLE_FIELD_VALIDATE_ON_SET_VALUE = bool(
  os.getenv('PY_SGORM_DISABLE_FIELD_VALIDATE_ON_SET_VALUE', False)
)

################################################################################
#
# Enables field query profiling.
#
# Field query profiling allows you run your Python code that uses the ORM
# and afterwards inspect which fields were queried from the database that arent
# set as default fields to request.
#
################################################################################

ENABLE_FIELD_QUERY_PROFILING = bool(
  os.getenv('PY_SGORM_ENABLE_FIELD_QUERY_PROFILING', False)
)

################################################################################
#
# Enables field names to be included in the results of dir(SgEntity).
#
################################################################################

ENTITY_DIR_INCLUDE_FIELDS = bool(
  os.getenv('PY_SGORM_ENTITY_DIR_INCLUDE_FIELDS', True)
)

################################################################################
#
# IMPORTANT!
# All registered entity base classes must derive from SgEntity!
#
################################################################################

# Do not remove the entry for "Entity"!  This is the class used for all
# un-definied Entity types.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=ShotgunORM.SgEntity,
  sgEntityTypes=['Entity']
)

################################################################################
#
# Config for the default fields to fill in for Entities.
#
# To configure an Entity to pull all fields pass ['all'] to sgFields.
#
# To configure an Entity to pull no fields pass ['none'] or [] to sgFields.
#
################################################################################

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='ApiUser',
  sgQueryTemplates=['default'],
  sgFields=[
    'description',
    'firstname',
    'lastname'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Asset',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'project',
    'sg_asset_type'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Attachment',
  sgQueryTemplates=['default'],
  sgFields=[
    'description',
    'display_name',
    'filename',
    'project',
    'sg_type',
    'this_file'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Booking',
  sgQueryTemplates=['default'],
  sgFields=[
    'end_date',
    'note',
    'project',
    'start_date'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Department',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'department_type',
    'name'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='EventLogEntry',
  sgQueryTemplates=['default'],
  sgFields=[
    'attribute_name',
    'created_at',
    'description',
    'entity',
    'event_type',
    'meta',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Group',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'users'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='HumanUser',
  sgQueryTemplates=['default'],
  sgFields=[
    'department',
    'email',
    'name',
    'projects'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Icon',
  sgQueryTemplates=['default'],
  sgFields=[
    'html',
    'icon_type',
    'image',
    'url'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='LocalStorage',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'description',
    'linux_path',
    'mac_path',
    'windows_path'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Note',
  sgQueryTemplates=['default'],
  sgFields=[
    'content',
    'created_at',
    'created_by',
    'note_links',
    'project',
    'replies',
    'reply_content',
    'subject',
    'tasks',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Page',
  sgQueryTemplates=['default'],
  sgFields=[
    'admin',
    'description',
    'entity_type',
    'folder',
    'name',
    'page_type',
    'project',
    'shared'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='PageHit',
  sgQueryTemplates=['default'],
  sgFields=[
    'created_at',
    'page',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='PageSetting',
  sgQueryTemplates=['default'],
  sgFields=[
    'page',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='PermissionRuleSet',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'display_name',
    'entity_type',
    'parent_set'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Phase',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'description',
    'project'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Playlist',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'project',
    'versions'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Project',
  sgQueryTemplates=['default'],
  sgFields=[
    'name',
    'phases'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Reply',
  sgQueryTemplates=['default'],
  sgFields=[
    'content',
    'created_at',
    'entity',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Sequence',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'project',
    'shots'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Shot',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'project',
    'sg_sequence'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Status',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'name',
    'updated_at',
    'updated_by'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Step',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'short_name'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Task',
  sgQueryTemplates=['default'],
  sgFields=[
    'content',
    'project',
    'sg_status_list',
    'step'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='TaskDependency',
  sgQueryTemplates=['default'],
  sgFields=[
    'dependent_task_id',
    'task',
    'task_id'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='TaskTemplate',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'description',
    'entity_type'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Ticket',
  sgQueryTemplates=['default'],
  sgFields=[
    'addressings_cc',
    'addressings_to',
    'created_at',
    'created_by',
    'description',
    'project',
    'replies',
    'sg_priority',
    'sg_status_list',
    'sg_ticket_type',
    'tickets',
    'title',
    'updated_at',
    'updated_by'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='TimeLog',
  sgQueryTemplates=['default'],
  sgFields=[
    'date',
    'entity',
    'project',
    'user'
  ]
)

ShotgunORM.SgSchema.registerDefaultQueryFields(
  sgEntityType='Version',
  sgQueryTemplates=['default'],
  sgFields=[
    'code',
    'project',
    'sg_first_frame',
    'sg_last_frame',
    'sg_path_to_frames'
  ]
)

################################################################################
#
# Config for the default schema fields to ignore for Entities.
#
################################################################################

ShotgunORM.SgSchema.ignoreEntityField(
  'HumanUser',
  'email_all_security',
  'global'
)

################################################################################
#
# Overriding the level of Loggers.
#
# Note:
# Loggers by default look for an env var to set their runlevel to if present.
# See the ShotgunORM.ShotgunORMLogger for more info on what env vars to set.
#
################################################################################

#import logging
#
#ShotgunORM.LoggerAsyncSearchEngine.setLevel(logging.DEBUG)
#ShotgunORM.LoggerCallback.setLevel(logging.DEBUG)
#ShotgunORM.LoggerConnection.setLevel(logging.DEBUG)
#ShotgunORM.LoggerEntity.setLevel(logging.DEBUG)
#ShotgunORM.LoggerEventWatcher.setLevel(logging.DEBUG)
#ShotgunORM.LoggerField.setLevel(logging.DEBUG)
#ShotgunORM.LoggerFactory.setLevel(logging.DEBUG)
#ShotgunORM.LoggerORM.setLevel(logging.DEBUG)
#ShotgunORM.LoggerQueryEngine.setLevel(logging.DEBUG)
#ShotgunORM.LoggerSchema.setLevel(logging.DEBUG)
#ShotgunORM.LoggerScriptEngine.setLevel(logging.DEBUG)
#
#del logging

################################################################################
#
# USER CUSTOMIZATIONS START HERE!
#
################################################################################

user_cfg = os.path.sep.join([os.path.dirname(__file__), 'user.py'])

if os.path.exists(user_cfg):
  import user

################################################################################
#
# CLEANUP
#
################################################################################

del user_cfg
del os
