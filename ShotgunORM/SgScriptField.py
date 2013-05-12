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
  'SgScriptField'
]

class SgScriptField(object):
  '''
  Base Script engine field.
  '''

  __scriptfields__ = {}

  @classmethod
  def registerScriptField(self, sgFieldReturnType, sgScriptField):
    '''
    Registers a script field.
    '''

    self.__scriptfields__[sgFieldReturnType] = sgScriptField

  def __eq__(self, value):
    raise RuntimeError('un-supported field operator')

  def __ne__(self, value):
    raise RuntimeError('un-supported field operator')

  def __lt__(self, value):
    raise RuntimeError('un-supported field operator')

  def __gt__(self, value):
    raise RuntimeError('un-supported field operator')

  def __contains__(self, value):
    raise RuntimeError('un-supported field operator')

  def between(self, a, b):
    raise RuntimeError('un-supported field operator')

  def contains(self, value):
    raise RuntimeError('un-supported field operator')

  def endswith(self, value):
    raise RuntimeError('un-supported field operator')

  def in_day(self, value):
    raise RuntimeError('un-supported field operator')

  def in_last(self, n, t):
    raise RuntimeError('un-supported field operator')

  def in_month(self, value):
    raise RuntimeError('un-supported field operator')

  def in_next(self, n, t):
    raise RuntimeError('un-supported field operator')

  def in_week(self, value):
    raise RuntimeError('un-supported field operator')

  def in_year(self, value):
    raise RuntimeError('un-supported field operator')

  def name_contains(self, value):
    raise RuntimeError('un-supported field operator')

  def name_endswith(self, value):
    raise RuntimeError('un-supported field operator')

  def name_startswith(self, value):
    raise RuntimeError('un-supported field operator')

  def startswith(self, value):
    raise RuntimeError('un-supported field operator')

  def type(self, value):
    raise RuntimeError('un-supported field operator')
