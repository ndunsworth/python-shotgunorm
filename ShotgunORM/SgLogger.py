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
  'SgLogger',
  'LoggerCallback',
  'LoggerConnection',
  'LoggerEntity',
  'LoggerEntityField',
  'LoggerFactory',
  'LoggerSchema',
  'LoggerScriptEngine',
  'LoggerSession'
]

# Python imports
import logging
import os

LoggerCallback = None
LoggerConnection = None
LoggerEntity = None
LoggerEntityField = None
LoggerFactory = None
LoggerSchema = None
LoggerScriptEngine = None
LoggerSession = None

class SgLogger(logging.Logger):
  '''
  Custom logging.Logger used by the ShotgunORM library.

  Note:
  To enable a particular loggers debug level you can set a env var according to
  the following format.

  SgCallbacks            debug: PY_SHOTGUNORM_SGCALLBACK_DEBUG=1
  SgConnection           debug: PY_SHOTGUNORM_SGCONNECTION_DEBUG=1
  SgSchema               debug: PY_SHOTGUNORM_SGSCHEMA_DEBUG=1
  SgEntityClassFactory   debug: PY_SHOTGUNORM_SGENTITYCLASSFACTORY_DEBUG=1
  SgSession              debug: PY_SHOTGUNORM_SGSESSION_DEBUG=1
  SgScriptEngine         debug: PY_SHOTGUNORM_SGENTITYFIELD_DEBUG=1
  SgEntity               debug: PY_SHOTGUNORM_SGENTITY_DEBUG=1
  SgField                debug: PY_SHOTGUNORM_SGENTITYFIELD_DEBUG=1
  '''

  def __init__(self, name, level=None):
    if level == None:
      envEnable = os.getenv('PY_SHOTGUNORM_%s_DEBUG' % name.upper(), logging.INFO)

      if int(envEnable) == 1:
        level = logging.DEBUG
      else:
        level = logging.INFO

    # Python 2.6 fix
    try:
      super(SgLogger, self).__init__(name, level)
    except TypeError:
      logging.Logger.__init__(self, name, level)

    self._logStreamHandler = logging.StreamHandler()
    self._formatter = logging.Formatter('[%(levelname)s:SGORM:%(name)s] %(message)s')

    self._logStreamHandler.setFormatter(self._formatter)

    self.addHandler(self._logStreamHandler)

LoggerCallback = SgLogger('SgCallback')
LoggerEntity = SgLogger('SgEntity')
LoggerEntityField = SgLogger('SgField')
LoggerFactory = SgLogger('SgEntityClassFactory')
LoggerSchema = SgLogger('SgSchema')
LoggerScriptEngine = SgLogger('SgScriptEngine')
LoggerSession = SgLogger('SgSession')
