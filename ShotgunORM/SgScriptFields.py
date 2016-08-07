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
  'SgScriptFieldCheckbox',
  'SgScriptFieldColor',
  'SgScriptFieldColor2',
  'SgScriptFieldDate',
  'SgScriptFieldDateTime',
  'SgScriptFieldEntity',
  'SgScriptFieldEntityMulti',
  'SgScriptFieldFloat',
  'SgScriptFieldInt',
  'SgScriptFieldSelectionList',
  'SgScriptFieldTagList',
  'SgScriptFieldText'
]

# Python imports
import types

# This module imports
import ShotgunORM

class SgScriptFieldCheckbox(ShotgunORM.SgScriptField):
  '''
  Script engine checkbox field class.
  '''

  def __eq__(self, value):
    if value != None:
      try:
        value = bool(value)
      except:
        raise TypeError('expected a bool, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if value != None:
      try:
        value = bool(value)
      except:
        raise TypeError('expected a bool, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

class SgScriptFieldColor(ShotgunORM.SgScriptField):
  '''
  Script engine color field class.
  '''

  def __eq__(self, value):
    if value != None:
      if isinstance(value, str):
        pass
      elif isinstance(value, (list, tuple)):
        if len(value) != 3:
          raise ValueError('list requires exactly 3 elements')

        value = '%s,%s,%s' % tuple(value)
      else:
        raise TypeError('expected a str or list of ints, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if not isinstance(value, types.NoneType):
      if isinstance(value, str):
        pass
      elif isinstance(value, (list, tuple)):
        if len(value) != 3:
          raise ValueError('list requires exactly 3 elements')

        value = '%s,%s,%s' % tuple(value)
      else:
        raise TypeError('expected a str or list of ints, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

class SgScriptFieldColor2(SgScriptFieldColor):
  '''
  Script engine color2 field class.
  '''

  pass

class SgScriptFieldDate(ShotgunORM.SgScriptField):
  '''
  Script engine date field class.
  '''

  def __eq__(self, value):
    if not isinstance(value, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if not isinstance(value, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def __lt__(self, value):
    if not isinstance(value, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'less_than',
      'neop': None
    }

  def __gt__(self, value):
    if not isinstance(value, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'greater_than',
      'neop': None
    }

  def _in(self, value):
    if isinstance(value, (list, tuple)):
      if not all(isinstance(x, (datetime.datetime, str)) for x in value):
        raise TypeError('expected (datetime, str, None) in list')
    elif not isinstance(value, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in',
      'neop': 'not_in'
    }

  def between(self, a, b):
    if not isinstance(a, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    if not isinstance(b, (datetime.datetime, str, types.NoneType)):
      raise TypeError('expected (datetime, str, None), got %s' % type(value).__name__)

    return {
      'value': [a, b],
      'op': 'between',
      'neop': 'not_between'
    }

  def in_day(self, value):
    try:
      value = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in_calendar_day',
      'neop': None
    }

  def in_last(self, n, t):
    if not t in ['HOUR','DAY', 'WEEK', 'MONTH', 'YEAR']:
      raise ValueError('invalid time spec "%s", valid %s' % (t, ['HOUR','DAY', 'WEEK', 'MONTH', 'YEAR']))

    try:
      n = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(n).__name__)

    return {
      'value': [n, t],
      'op': 'in_last',
      'neop': 'not_in_last'
    }

  def in_month(self, value):
    try:
      value = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in_calendar_month',
      'neop': None
    }

  def in_next(self, n, t):
    if not t in ['HOUR','DAY', 'WEEK', 'MONTH', 'YEAR']:
      raise ValueError('invalid time spec "%s", valid %s' % (t, ['HOUR','DAY', 'WEEK', 'MONTH', 'YEAR']))

    try:
      n = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(n).__name__)

    return {
      'value': [n, t],
      'op': 'in_next',
      'neop': 'not_in_next'
    }

  def in_week(self, value):
    try:
      value = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in_calendar_week',
      'neop': None
    }

  def in_year(self, value):
    try:
      value = int(n)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in_calendar_year',
      'neop': None
    }

class SgScriptFieldDateTime(SgScriptFieldDate):
  '''
  Script engine datetime field class.
  '''

  pass

class SgScriptFieldEntity(ShotgunORM.SgScriptField):
  '''
  Script engine entity field class.
  '''

  def _in(self, value):
    if isinstance(value, (list, tuple)):
      if not all(isinstance(x, (ShotgunORM.SgEntity, dict)) for x in value):
        raise TypeError('expected (ShotgunORM.SgEntity, dict, list in list')

      tmp = []

      for i in value:
        try:
          tmp.append(i.toEntityFieldData())
        except AttributeError:
          tmp.append(i)

      value = tmp
    elif isinstance(value, ShotgunORM.SgEntity):
      value = [value.toEntityFieldData()]
    elif isinstance(value, dict):
      value = [value]
    else:
      raise TypeError('expected (ShotgunORM.SgEntity, dict, list), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in',
      'neop': 'not_in'
    }

  def __eq__(self, value):
    if isinstance(value, (dict, types.NoneType)):
      pass
    elif isinstance(value, ShotgunORM.SgEntity):
      value = value.toEntityFieldData()
    else:
      raise TypeError('expected a (ShotgunORM.SgEntity, dict, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if isinstance(value, (dict, types.NoneType)):
      pass
    elif isinstance(value, ShotgunORM.SgEntity):
      value = value.toEntityFieldData()
    else:
      raise TypeError('expected a (ShotgunORM.SgEntity, dict, None), got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def name_contains(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'name_contains',
      'neop': 'name_not_contains'
    }

  def name_is(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'name_is',
      'neop': None
    }

  def type(self, value):
    if value != None:
      if isinstance(value, ShotgunORM.SgEntity):
        value = value.type
      elif not isinstance(value, str):
        raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'type_is',
      'neop': 'type_is_not'
    }

class SgScriptFieldEntityMulti(SgScriptFieldEntity):
  '''
  Script engine entity-multi field class.
  '''

  def name_is(self, value):
    raise RuntimeError('function not supported')

class SgScriptFieldFloat(ShotgunORM.SgScriptField):
  '''
  Script engine float field class.
  '''

  def __eq__(self, value):
    if value != None:
      try:
        value = float(value)
      except:
        raise TypeError('expected a float, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if value != None:
      try:
        value = float(value)
      except:
        raise TypeError('expected a float, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def __lt__(self, value):
    try:
      value = float(value)
    except:
      raise TypeError('expected a float, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'less_than',
      'neop': None
    }

  def __gt__(self, value):
    try:
      value = float(value)
    except:
      raise TypeError('expected a float, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'greater_than',
      'neop': None
    }

  def _in(self, value):
    if isinstance(value, (list, tuple)):
      tmp = []

      try:
        for i in value:
          tmp.append(float(i))
      except:
        raise TypeError('expected a list of floats, %s' % value)

      value = tmp
    else:
      try:
        value = float(value)
      except:
        raise TypeError('expected a float, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in',
      'neop': 'not_in'
    }

  def between(self, a, b):
    try:
      a = float(a)
    except:
      raise TypeError('expected a float, got %s' % type(a).__name__)

    try:
      b = float(b)
    except:
      raise TypeError('expected a float, got %s' % type(b).__name__)

    return {
      'value': [a, b],
      'op': 'between',
      'neop': 'not_between'
    }

class SgScriptFieldInt(ShotgunORM.SgScriptField):
  '''
  Script engine int field class.
  '''

  def __eq__(self, value):
    if value != None:
      try:
        value = int(value)
      except:
        raise TypeError('expected a int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if value != None:
      try:
        value = int(value)
      except:
        raise TypeError('expected a int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def __lt__(self, value):
    try:
      value = int(value)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'less_than',
      'neop': None
    }

  def __gt__(self, value):
    try:
      value = int(value)
    except:
      raise TypeError('expected an int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'greater_than',
      'neop': None
    }

  def _in(self, value):
    if isinstance(value, (list, tuple)):
      tmp = []

      try:
        for i in value:
          tmp.append(int(i))
      except:
        raise TypeError('expected a list of int, %s' % value)

      value = tmp
    else:
      try:
        value = int(value)
      except:
        raise TypeError('expected a int, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'in',
      'neop': 'not_in'
    }

  def between(self, a, b):
    try:
      a = int(a)
    except:
      raise TypeError('expected a int, got %s' % type(a).__name__)

    try:
      b = int(b)
    except:
      raise TypeError('expected a int, got %s' % type(b).__name__)

    return {
      'value': [a, b],
      'op': 'between',
      'neop': 'not_between'
    }

class SgScriptFieldText(ShotgunORM.SgScriptField):
  '''
  Script engine text field class.
  '''

  def __eq__(self, value):
    if not isinstance(value, (str, types.NoneType)):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if not isinstance(value, (str, types.NoneType)):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def _in(self, value):
    if isinstance(value, (list, tuple)):
      if not all(isinstance(x, str) for x in value):
        raise TypeError('expected a list of strings')

    return {
      'value': value,
      'op': 'in',
      'neop': 'not_in'
    }

  def contains(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'contains',
      'neop': 'not_contains'
    }

  def endswith(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'ends_with',
      'neop': None
    }

  def startswith(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'starts_with',
      'neop': None
    }

class SgScriptFieldSelectionList(SgScriptFieldText):
  '''
  Script engine selection list field class.
  '''

  pass

class SgScriptFieldTagList(ShotgunORM.SgScriptField):
  '''
  Script engine tag list field class.
  '''

  def __eq__(self, value):
    if not isinstance(value, (str, types.NoneType)):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is',
      'neop': None
    }

  def __ne__(self, value):
    if not isinstance(value, (str, types.NoneType)):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'is_not',
      'neop': None
    }

  def name_contains(self, value):
    if not isinstance(value, str):
      raise TypeError('expected a str, got %s' % type(value).__name__)

    return {
      'value': value,
      'op': 'name_contains',
      'neop': 'name_not_contains'
    }
