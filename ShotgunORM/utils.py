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
  'facilityNameFromUrl',
  'formatSerializable',
  'mkEntityString',
  'mkEntityFieldString',
  'printSerializable',
  'sgApiInfo',
  'webUrlSgApi',
  'webUrlSgORM'
]

# Python imports
import re
import webbrowser

# This module imports
import ShotgunORM

REGEXP_PARSE_FACILITY = re.compile(
  r'(http(?:s?)://)([a-zA-Z\d]+)\.(shotgunstudio\.com.*)'
)

def facilityNameFromUrl(url):
  '''
  Returns the facility name from a Shotgun url.

  Example:
    print facilityNameFromUrl("https://leetstudios.shotgunstudio.com")

    result: "leetstudios"
  '''

  match = REGEXP_PARSE_FACILITY.search(url)

  if match == None:
    return 'unknown'
  else:
    return match.group(2)

def formatDict(obj, indent=0, indentSize=2, indentChar=' '):
  if len(obj) <= 0:
    return '%s{}' % mkIndent(indent, indentSize, indentChar)

  result = '%s{\n' % mkIndent(indent, indentSize, indentChar)

  keys = []

  #result.append('{')

  for key, value in obj.items():
    if isinstance(key, str):
      s = "%s'%s': " % (mkIndent(indent + 1, indentSize, indentChar), key)
    else:
      s = '%s%s: ' % (mkIndent(indent + 1, indentSize, indentChar), key)

    o = formatSerializable(value, indent + 1, indentSize, indentChar)

    indentSpan = (indentChar * indentSize)

    while o.startswith(indentSpan):
      o = o[len(indentSpan):]

    s += o

    keys.append(s)

  result += ',\n'.join(keys)

  result += '\n%s}' % mkIndent(indent, indentSize, indentChar)

  return result

def formatList(obj, indent=0, indentSize=2, indentChar=' '):
  if len(obj) <= 0:
    return '%s[]' % mkIndent(indent, indentSize, indentChar)

  result = '%s[\n' % mkIndent(indent, indentSize, indentChar)

  items = []

  for i in obj:
    s = formatSerializable(i, indent + 1, indentSize, indentChar)

    indentSpan = (indentChar * indentSize)

    while s.startswith(indentSpan):
      s = s[len(indentSpan):]

    s = '%s%s' % (mkIndent(indent + 1, indentSize, indentChar), s)

    items.append(s)

  result += ',\n'.join(items)

  result += '\n%s]' % mkIndent(indent, indentSize, indentChar)

  return result

def formatSet(obj, indent=0, indentSize=2, indentChar=' '):
  if len(obj) <= 0:
    return '%s{}' % mkIndent(indent, indentSize, indentChar)

  result = '%s{\n' % mkIndent(indent, indentSize, indentChar)

  items = []

  for i in obj:
    s = formatSerializable(i, indent + 1, indentSize, indentChar)

    indentSpan = (indentChar * indentSize)

    while s.startswith(indentSpan):
      s = s[len(indentSpan):]

    s = '%s%s' % (mkIndent(indent + 1, indentSize, indentChar), s)

    items.append(s)

  result += ',\n'.join(items)

  result += '\n%s}' % mkIndent(indent, indentSize, indentChar)

  return result

def formatTuple(obj, indent=0, indentSize=2, indentChar=' '):
  if len(obj) <= 0:
    return '%s()' % mkIndent(indent, indentSize, indentChar)

  result = '%s(\n' % mkIndent(indent, indentSize, indentChar)

  items = []

  for i in obj:
    s = formatSerializable(i, indent + 1, indentSize, indentChar)

    indentSpan = (indentChar * indentSize)

    while s.startswith(indentSpan):
      s = s[len(indentSpan):]

    s = '%s%s' % (mkIndent(indent + 1, indentSize, indentChar), s)

    items.append(s)

  result += ',\n'.join(items)

  result += '\n%s)' % mkIndent(indent, indentSize, indentChar)

  return result

def formatSerializable(obj, indent=0, indentSize=2, indentChar=' '):
  '''
  Converts the serializeble list/dict into a user friendly string better than
  pretty print.

  Args:
    * (obj) obj:
      Serializable Python object

    * (int) indent:
      Indentation level.

    * (int) indentSize:
      The string length of a single indent.  The arg "indentChar" is multiplied
      by this value.

    * (str) indentChar:
      Char used to represent an indent.
  '''

  result = ''

  if isinstance(obj, dict):
    result = formatDict(obj, indent, indentSize, indentChar)
  elif isinstance(obj, list):
    result = formatList(obj, indent, indentSize, indentChar)
  elif isinstance(obj, set):
    result = formatSet(obj, indent, indentSize, indentChar)
  elif isinstance(obj, tuple):
    result = formatTuple(obj, indent, indentSize, indentChar)
  else:
    result = repr(obj)

  return result

################################################################################
#
# Example
#
################################################################################

#logicalOp = {'conditions': [{'conditions': [{'path': 'id',
#     'relation': 'is_not',
#     'values': [10]},
#    {'path': 'code', 'relation': 'contains', 'values': ['building']}],
#   'logical_operator': 'and'},
#  {'conditions': [{'path': 'id', 'relation': 'between', 'values': [100, 200]},
#    {'path': 'code', 'relation': 'contains', 'values': ['misc']}],
#   'logical_operator': 'and'},
#  {'path': 'project',
#   'relation': 'is',
#   'values': [{'id': 65, 'type': 'Project'}]}],
# 'logical_operator': 'or'}
#
#print formatSerializable(logicalOp)

def mkEntityString(sgEntity):
  '''
  Returns a string formatted for the Entity.
  '''

  result = 'Shotgun'

  if sgEntity.hasField('project'):
    result += '.Project'

  iD = sgEntity['id']

  if sgEntity.isCustom():
    result += '.%s(id:%d)' % (sgEntity.__classinfo__.label(), iD)
  else:
    result += '.%s(id:%d)' % (sgEntity.type, iD)

  return result

def mkEntityFieldString(sgEntityField):
  '''
  Returns a string formatted for the Entity field.
  '''

  parent = sgEntityField.parentEntity()

  result = ''

  if parent == None:
    result = '%s.Field("%s")' % (
      type(sgEntityField).__name__,
      sgEntityField.name()
    )
  else:
    result = mkEntityString(sgEntityField.parentEntity())

    result += '.Field("%s")' % sgEntityField.name()

  return result

def mkIndent(indent, indentSize, indentChar):
  '''
  Returns a indentation string.

  Args:
    * (int) indent:
      Indentation level.

    * (int) indentSize:
      The string length of a single indent.  The arg "indentChar" is multiplied
      by this value.

    * (str) indentChar:
      Char used to represent an indent.
  '''

  return (indentChar * indentSize) * indent

def printSerializable(obj, indent=0, indentSize=2, indentChar=' '):
  '''
  Prints the serializable list/dict as a user friendly string better than pretty
  print.

  Useful for debuging logical operator search filters.

  Args:
    * (obj) obj:
      Serializable Python object

    * (int) indent:
      Indentation level.

    * (int) indentSize:
      The string length of a single indent.  The arg "indentChar" is multiplied
      by this value.

    * (str) indentChar:
      Char used to represent an indent.
  '''
  
  print formatSerializable(obj, indent, indentSize, indentChar)

def sgApiInfo():
  '''
  Returns a SgApiInfo object.
  '''

  return ShotgunORM.SgApiInfo()

def webUrlSgApi(openInBrowser=False):
  '''
    Returns the Shotgun API URL.

    Args:
      * (bool) openInBrowser:
        When True the URL will be opened in the operating systems default
        web-browser.
  '''

  url = 'https://github.com/shotgunsoftware/python-api'

  if openInBrowser:
    webbrowser.open(url)

  return url

def webUrlSgORM(openInBrowser=False):
  '''
    Returns the ShotgunORM API URL.

    Args:
      * (bool) openInBrowser:
        When True the URL will be opened in the operating systems default
        web-browser.
  '''

  url = 'https://github.com/shotgunsoftware/python-shotgunorm'

  if openInBrowser:
    webbrowser.open(url)

  return url
