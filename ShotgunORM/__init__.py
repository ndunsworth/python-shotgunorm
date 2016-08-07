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
  '__version__',
  'MAJOR_VERSION',
  'MINOR_VERSION',
  'RELEASE_VERSION',
  'VERSION',
  'SHOTGUN_API',
  'SHOTGUN_API_LOCK',
  'SgAbstractSearchIterator',
  'SgApiInfo',
  'SgAsyncSearchEngine',
  'SgAsyncSearchResult',
  'SgBufferedSearchIterator',
  'SgConnection',
  'SgConnectionMeta',
  'SgEntity',
  'SgEntityClassFactory',
  'SgEntitySchemaInfo',
  'SgField',
  'SgFieldSchemaInfo',
  'SgQueryEngine',
  'SgSchema',
  'SgScriptField',
  'SgSearchIterator',
  'parseFromLogicalOp',
  'parseToLogicalOp',
  'config'
]

MAJOR_VERSION = 1
MINOR_VERSION = 0
RELEASE_VERSION = 1

VERSION = '%(major)d.%(minor)dv%(release)d' % {
  'major': MAJOR_VERSION,
  'minor': MINOR_VERSION,
  'release': RELEASE_VERSION
}

__version__ = VERSION

import threading

SHOTGUN_API_LOCK = threading.RLock()

del threading

################################################################################
#
# Import Loggers
#
################################################################################

import SgLogger

__all__.extend(SgLogger.__all__)

del SgLogger

from SgLogger import *

################################################################################
#
# Import utils
#
################################################################################

import utils

__all__.extend(utils.__all__)

del utils

from utils import *

################################################################################
#
# Import schema, connection and engine related classes
#
################################################################################

from SgApiInfo import SgApiInfo
from SgServerInfo import SgServerInfo
from SgConnection import SgConnection, SgConnectionMeta
from SgEntityClassFactory import SgEntityClassFactory
from SgAsyncSearchEngine import SgAsyncSearchEngine, SgAsyncSearchResult
from SgQueryEngine import SgQueryEngine
from SgSchema import SgSchema
from SgSearchIterator import SgAbstractSearchIterator, SgBufferedSearchIterator, SgSearchIterator

import SgUndo

__all__.extend(SgUndo.__all__)

del SgUndo

from .SgUndo import *

################################################################################
#
# Import Entities and fields
#
################################################################################

from SgEntity import SgEntity, SgEntitySchemaInfo
from SgField import SgField, SgFieldSchemaInfo

# Fields
import SgFields

__all__.extend(SgFields.__all__)

del SgFields

from SgFields import *

################################################################################
#
# Import scripting engine and script fields
#
################################################################################

from SgScriptField import SgScriptField

import SgScriptFields

__all__.extend(SgScriptFields.__all__)

del SgScriptFields

from SgScriptFields import *

from SgScriptEngine import convertToLogicalOp, parseFromLogicalOp, parseToLogicalOp

################################################################################
#
# Import event monitor
#
################################################################################

import SgEventWatcher

__all__.extend(SgEventWatcher.__all__)

del SgEventWatcher

from SgEventWatcher import *

import SgEventWatchers

__all__.extend(SgEventWatchers.__all__)

del SgEventWatchers

from SgEventWatchers import *

################################################################################
#
# Import callbacks
#
################################################################################

import callbacks

__all__.extend(callbacks.__all__)

del callbacks

from callbacks import *

################################################################################
#
# Import the user configuration
#
################################################################################

import config

SHOTGUN_API = None

try:
  SHOTGUN_API = __import__(config.SHOTGUNAPI_NAME)
except Exception, e:
  if e.message == 'No module named %s' % config.SHOTGUNAPI_NAME:
    raise ImportError('ShotgunORM unable to find Shotgun Python API module "%s", check "./ShotgunORM/__init__.SHOTGUNAPI_NAME" or sys.path' % config.SHOTGUNAPI_NAME)
  else:
    raise e
