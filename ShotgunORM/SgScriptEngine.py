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
  'convertToLogicalOp',
  'parseLogicalOp',
  'parseSearchExp'
]

# Python imports
import copy
import exceptions
import re

# This module imports
import ShotgunORM

OP_AND = ' and '
OP_OR = ' or '
OP_AND_STRIP = 'and'
OP_OR_STRIP = 'or'

class SgScriptError(exceptions.Exception):
  '''
  General script engine exception.
  '''

  pass

def cleanSearchExp(sgSearchExp):
  '''
  Returns the passed search expression cleaned up of extra spaces.

  Also throws when closing parentheses and quotes are not present.
  '''

  backwardParenCount = 0
  backwardQuoteCount = 0

  index = 0

  curWord = ''

  for c in sgSearchExp:
    if backwardParenCount < 0:
      raise SgScriptError('"%s" missing closing parentheses' % curWord)

    if c == '(':
      if backwardQuoteCount <= 0:
        backwardParenCount += 1

      curWord += c
    elif c == ')':
      if backwardQuoteCount <= 0:
        backwardParenCount -= 1

      if backwardQuoteCount <= 0 and curWord.endswith(' '):
        curWord = curWord[:-1] + c
      else:
        curWord += c
    elif c == '"' or c == "'":
      backwardQuoteCount += 1

      if backwardQuoteCount >= 2:
        backwardQuoteCount = 0

      curWord += c
    elif c == ' ':
      if len(curWord) <= 0:
        continue

      if curWord.endswith('(') and backwardQuoteCount <= 0:
        continue

      if backwardQuoteCount >= 1 or not curWord.endswith(' '):
        curWord += c
    else:
      curWord += c

  if backwardParenCount != 0:
    raise SgScriptError('"%s" missing closing parentheses' % curWord)

  result = curWord.strip()

  if backwardQuoteCount >= 1:
    raise SgScriptError('"%s" missing closing quote' % curWord)

  #ShotgunORM.LoggerScriptEngine.debug('ShotgunORM.SgScriptEngine.cleanSearchExp(...)')
  #ShotgunORM.LoggerScriptEngine.debug('    * before: "%(searchExp)s"', {'searchExp': sgSearchExp})
  #ShotgunORM.LoggerScriptEngine.debug('    * after: "%(searchExp)s"', {'searchExp': result})

  return result

def buildSearchExpSpan(sgSearchExp):
  '''
  Returns the next span in a search expression.
  '''

  if sgSearchExp.startswith(OP_AND):
    return OP_AND
  elif sgSearchExp.startswith(OP_OR):
    return OP_OR

  if sgSearchExp.startswith('('):
    backwardParenCount = 0
    backwardQuoteCount = 0

    index = -1

    for c in sgSearchExp:
      index += 1

      if c == '(':
        if backwardQuoteCount <= 0:
          backwardParenCount += 1
      elif c == ')':
        if backwardQuoteCount <= 0:
          backwardParenCount -= 1

        if backwardParenCount == 0:
          break
      elif c == '"' or c == "'":
        backwardQuoteCount += 1

        if backwardQuoteCount >= 2:
          backwardQuoteCount = 0

    result = sgSearchExp[:index + 1]

    if result.endswith(' and)') or result.endswith(' or)'):
      raise SgScriptError('"%s" invalid search expression span' % result)

    return result
  else:
    backwardParenCount = 1
    backwardQuoteCount = 0

    curWord =  ''

    for c in sgSearchExp:
      if c == '(':
        if backwardQuoteCount <= 0:
          backwardParenCount += 1
      elif c == ')':
        if backwardQuoteCount <= 0:
          backwardParenCount -= 1
      elif c == '"' or c == "'":
        backwardQuoteCount += 1

        if backwardQuoteCount >= 2:
          backwardQuoteCount = 0

      if backwardQuoteCount <= 0 and len(curWord) >= 4:
        if curWord.endswith(OP_AND):
          curWord = curWord[:-5]

          break
        elif curWord.endswith(OP_OR):
          curWord = curWord[:-4]

          break

      curWord += c

    result = curWord

    if result.endswith(' and') or result.endswith(' or'):
      raise SgScriptError('"%s" invalid search expression span' % result)

    return result

def splitSearchExp(sgSearchExp):
  '''
  Splits a search expression into its spans.
  '''

  searchPattern = sgSearchExp

  result = []

  while len(searchPattern) >= 1:
    span = buildSearchExpSpan(searchPattern)

    searchPattern = searchPattern[len(span):]

    result.append(span)

  return result

EXPRESSION_SUPPORTS_IN = [
  ShotgunORM.SgField.RETURN_TYPE_DATE,
  ShotgunORM.SgField.RETURN_TYPE_DATE_TIME,
  ShotgunORM.SgField.RETURN_TYPE_ENTITY,
  ShotgunORM.SgField.RETURN_TYPE_FLOAT,
  ShotgunORM.SgField.RETURN_TYPE_INT,
  ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY,
  ShotgunORM.SgField.RETURN_TYPE_TEXT
]

SCRIPT_FIELDS = {
  ShotgunORM.SgField.RETURN_TYPE_CHECKBOX: ShotgunORM.SgScriptFieldCheckbox(),
  ShotgunORM.SgField.RETURN_TYPE_COLOR: ShotgunORM.SgScriptFieldColor(),
  ShotgunORM.SgField.RETURN_TYPE_COLOR2: ShotgunORM.SgScriptFieldColor2(),
  ShotgunORM.SgField.RETURN_TYPE_DATE: ShotgunORM.SgScriptFieldDate(),
  ShotgunORM.SgField.RETURN_TYPE_DATE_TIME: ShotgunORM.SgScriptFieldDateTime(),
  ShotgunORM.SgField.RETURN_TYPE_ENTITY: ShotgunORM.SgScriptFieldEntity(),
  ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY: ShotgunORM.SgScriptFieldEntityMulti(),
  ShotgunORM.SgField.RETURN_TYPE_FLOAT: ShotgunORM.SgScriptFieldFloat(),
  ShotgunORM.SgField.RETURN_TYPE_INT: ShotgunORM.SgScriptFieldInt(),
  ShotgunORM.SgField.RETURN_TYPE_LIST: ShotgunORM.SgScriptFieldSelectionList(),
  ShotgunORM.SgField.RETURN_TYPE_TAG_LIST: ShotgunORM.SgScriptFieldTagList(),
  ShotgunORM.SgField.RETURN_TYPE_TEXT: ShotgunORM.SgScriptFieldText(),
}

def buildSearchExpFilter(sgEntityFieldInfos, sgArgs, sgSearchExpSpan):
  '''
  Builds a logical operator from a search expression span.
  '''

  if len(sgSearchExpSpan) <= 0:
    raise SgScriptError('search expression span empty')

  ShotgunORM.LoggerScriptEngine.debug('            - Parsing sub-span: "%(sgSearchExpSpan)s"', {'sgSearchExpSpan': sgSearchExpSpan})

  inverse = sgSearchExpSpan.startswith('!')

  if inverse:
    sgSearchExpSpan = sgSearchExpSpan[1:]
  else:
    if sgSearchExpSpan.startswith(' not '):
      inverse = True

      sgSearchExpSpan = sgSearchExpSpan[5:]

  index = 0

  for c in sgSearchExpSpan:
    if c in [' ', '.', '=', '<', '>', '!']:
      break

    index += 1

  fieldName = sgSearchExpSpan[:index]

  try:
    fieldInfo = sgEntityFieldInfos[fieldName]
  except KeyError:
    raise SgScriptError('"%s" invalid field name' % fieldName)

  try:
    scriptField = SCRIPT_FIELDS[fieldInfo.returnType()]
  except AttributeError:
    raise SgScriptError('field "%s" contains no scriptfield operator' % fieldName)

  globalEnv = {}

  localEnv = {
    'argv': sgArgs,
    fieldName: scriptField
  }

  # Python is lame as shit and doesnt return the value of calling __contains__
  # on a class.  If __contains__ returns anything other then None, False
  # it returns True.  So we cant use our wizardy with the script field class :(
  #
  # Correction for this problem follows.
  if fieldInfo.returnType() in EXPRESSION_SUPPORTS_IN:
    inString = '%s in ' % fieldName

    if sgSearchExpSpan.startswith(inString):
      a, b = sgSearchExpSpan.split(inString, 1)

      sgSearchExpSpan = '%s._in(%s)' % (fieldName, b)

  try:
    expResult = eval(sgSearchExpSpan, globalEnv, localEnv)
  except Exception as e:
    raise SgScriptError('"%s" %s' % (sgSearchExpSpan, e))

  if inverse and expResult['neop'] == None:
    raise SgScriptError('%s does not contain a not equal function' % sgSearchExpSpan)

  logicalCond = {
    'path' : fieldName,
    'relation' : None,
    'values' : expResult['value']
  }

  if not isinstance(logicalCond['values'], (list, tuple)):
    logicalCond['values'] = [logicalCond['values']]

  if inverse:
    logicalCond['relation'] = expResult['neop']
  else:
    logicalCond['relation'] = expResult['op']

  return [logicalCond]

def buildSearchExpFilters(sgEntityFieldInfos, sgArgs, sgSearchExpSpans):
  '''
  Builds the locial operator pattern from a search expression
  '''

  ShotgunORM.LoggerScriptEngine.debug('        + Parsing spans: %(sgSearchExpSpans)s', {'sgSearchExpSpans': sgSearchExpSpans})

  logicalConds = []
  logicalOp = {'logical_operator': None, 'conditions': logicalConds}

  if len(sgSearchExpSpans) <= 0:
    raise SgScriptError('empty search expression span')

  if sgSearchExpSpans[0] in [OP_AND, OP_OR]:
    raise SgScriptError('"%s" invalid search expression' % ' '.join(sgSearchExpSpans))

  if len(sgSearchExpSpans) == 1:
    span = sgSearchExpSpans[0]

    if span.startswith('('):
      while span.startswith('(') and span.endswith(')'):
        span = span[1:-1]

      return buildSearchExpFilters(
        sgEntityFieldInfos,
        sgArgs,
        splitSearchExp(span)
      )

  curOp = None

  for span in sgSearchExpSpans:
    if span in [OP_AND, OP_OR]:
      curOp = span

      if curOp == OP_AND:
        logicalOp['logical_operator'] = OP_AND_STRIP
      else:
        logicalOp['logical_operator'] = OP_OR_STRIP

      break

  if logicalOp['logical_operator'] == None:
    if len(sgSearchExpSpans) >= 2:
      raise SgScriptError('"%s" invalid search expression' % ' '.join(sgSearchExpSpans))
    else:
      logicalOp['logical_operator'] = OP_AND_STRIP

      curOp = OP_AND

  index = -1

  for span in sgSearchExpSpans:
    index += 1

    if span in [OP_AND, OP_OR]:
      if span != curOp:
        logicalOp = {'logical_operator': span.strip(), 'conditions': [logicalOp]}

        logicalOp['conditions'].append(
          buildSearchExpFilters(
            sgEntityFieldInfos,
            sgArgs,
            sgSearchExpSpans[index + 1:]
          )
        )

        return logicalOp

      continue

    if span.startswith('('):
      logicalConds.append(
        buildSearchExpFilters(
          sgEntityFieldInfos,
          sgArgs,
          splitSearchExp(span)
        )
      )
    else:
      logicalConds.extend(
        buildSearchExpFilter(sgEntityFieldInfos, sgArgs, span)
      )

  return logicalOp

def convertToLogicalOp(sgEntityInfo, sgSearchFilters, operator='and'):
  '''

  '''

  if sgSearchFilters == None or len(sgSearchFilters) <= 0:
    return []

  conditions = []

  for i in sgSearchFilters:
    field = i[0]
    info = sgEntityInfo.fieldInfo(field)

    if info == None:
      raise SgScriptError('invalid field name %s' % field)

    return_type = info.returnType()

    relation = i[1]

    try:
      script_field = SCRIPT_FIELDS[return_type]
    except KeyError:
      raise SgScriptError(
        'field "%s" contains no scriptfield operator' % field
      )

    script_func_info = LOG_TO_ORM_LOOKUP2.get(relation, None)

    if script_func_info == None:
      raise SgScriptError('invalid relation %s' % relation)

    script_func = getattr(script_field, script_func_info[0])

    values = i[2]

    try:
      expr_result = None

      if script_func_info[2] == True:
        if not isinstance(values, (list, tuple)) or len(values) != 2:
          raise SgScriptError(
            'invalid args for multi-arg operator, %s' % values
          )

        expr_result = script_func(*values)
      else:
        expr_result = script_func(values)
    except Exception as e:
      raise SgScriptError('%s %s' % (i, e))

    log_cond = {
      'path' : field,
      'relation' : None,
      'values' : expr_result['value']
    }

    if not isinstance(log_cond['values'], (list, tuple)):
      log_cond['values'] = [log_cond['values']]

    if script_func_info[1] == 'neop':
      log_cond['relation'] = expr_result['neop']
    else:
      log_cond['relation'] = expr_result['op']

    conditions.append(log_cond)

  return {
    'conditions': conditions,
    'logical_operator': operator
  }

def parseToLogicalOp(sgEntityInfo, sgSearchExp, sgArgs=[]):
  '''
  Parses a search expression and returns the Shotgun formated search filter.

  Args:
    * (SgEntitySchemaInfo) sgEntityInfo:
      SgEntitySchemaInfo that the search expression will reference.

    * (str) sgSearchExp:
      Search expression string.

    * (list) sgArgs:
      Args used when evaling search expression.
  '''

  if sgSearchExp == None:
    raise SgScriptError('expected a str got None')

  if len(sgSearchExp) <= 0 or sgSearchExp.isspace():
    raise SgScriptError('empty search string')

  ShotgunORM.LoggerScriptEngine.debug('# PARSING START')
  ShotgunORM.LoggerScriptEngine.debug('    * entity: "%(sgEntityType)s"', {'sgEntityType': sgEntityInfo.label()})
  ShotgunORM.LoggerScriptEngine.debug('    * search: "%(sgSearchExp)s"', {'sgSearchExp': sgSearchExp})

  try:
    sgSearchExp = cleanSearchExp(sgSearchExp)
  except SgScriptError, e:
    raise SgScriptError('%s in "%s"' % (e, sgSearchExp))

  try:
    searchExpSpans = splitSearchExp(sgSearchExp)
  except SgScriptError, e:
    raise SgScriptError('%s in "%s"' % (e, sgSearchExp))

  try:
    result = buildSearchExpFilters(sgEntityInfo.fieldInfos(), sgArgs, searchExpSpans)
  except SgScriptError, e:
    raise SgScriptError('%s in "%s"' % (e, sgSearchExp))

  ShotgunORM.LoggerScriptEngine.debug('# PARSING COMPLETE!')

  return result

LOG_TO_ORM_LOOKUP = {
  'is': '%(path)s == %(values)s',
  'is_not': '%(path)s != %(values)s',
  'less_than': '%(path)s > %(values)s',
  'greater_than': '%(path)s > %(values)s',
  'contains': '%(path)s.contains(%(values)s)',
  'not_contains': '!%(path)s.contains(%(values)s)',
  'starts_with': '%(path)s.startswith(%(values)s)',
  'ends_with': '%(path)s.endswith(%(values)s)',
  'between': '%(path)s.between(%(value1)s, %(value2)s)',
  'not_between': '!%(path)s.between(%(value1)s, %(value2)s)',
  'in_last': '%(path)s.in_last(%(value1)s, %(value2)s)',
  'not_in_last': '!%(path)s.in_last(%(value1)s, %(value2)s)',
  'in_next': '%(path)s.in_next(%(value1)s, %(value2)s)',
  'not_in_next': '!%(path)s.in_next(%(value1)s, %(value2)s)',
  'in': '%(path)s in %(values)s',
  'not_in': 'not %(path)s in %(values)s',
  'type_is': '%(path)s.type(%(values)s)',
  'type_is_not': '!%(path)s.type(%(values)s)',
  'in_calendar_day': '%(path)s.in_day(%(values)s)',
  'in_calendar_week': '%(path)s.in_week(%(values)s)',
  'in_calendar_month': '%(path)s.in_month(%(values)s)',
  'in_calendar_year': '%(path)s.in_year(%(values)s)',
  'name_contains': '%(path)s.name_contains(%(values)s)',
  'name_not_contains': '!%(path)s.name_contains(%(values)s)',
  'name_is': '%(path)s.name_is(%(values)s)',
}

LOG_TO_ORM_LOOKUP2 = {
  'is': ['__eq__', 'op', False],
  'is_not': ['__ne__', 'op', False],
  'less_than': ['__lt__', 'op', False],
  'greater_than': ['__gt__', 'op', False],
  'contains': ['contains', 'op', False],
  'not_contains': ['contains', 'neop', False],
  'starts_with': ['startswith', 'op', False],
  'ends_with': ['endswith', 'op', False],
  'between': ['between', 'op', True],
  'not_between': ['between', 'neop', True],
  'in_last': ['in_lastbetween', 'op', True],
  'not_in_last': ['in_lastbetween', 'neop', True],
  'in_next': ['in_next', 'op', True],
  'not_in_next': ['in_next', 'neop', True],
  'in': ['_in', 'op', False],
  'not_in': ['_in', 'neop', False],
  'type_is': ['type', 'op', False],
  'type_is_not': ['type', 'neop', False],
  'in_calendar_day': ['in_day', 'op', False],
  'in_calendar_week': ['in_week', 'op', False],
  'in_calendar_month': ['in_month', 'op', False],
  'in_calendar_year': ['in_year', 'op', False],
  'name_contains': ['name_contains', 'op', False],
  'name_not_contains': ['name_contains' 'neop', False],
  'name_is': ['name_is' 'op', False],
}

LOG_SINGLES = [
  'is',
  'is_not',
  'less_than',
  'greater_than',
  'contains',
  'starts_with',
  'ends_with',
  'type_is',
  'type_is_not',
  'name_contains',
  'name_is',
  'name_not_contains'
]

LOG_DOUBLES = [
  'between',
  'not_between',
  'in_last',
  'not_in_last',
  'in_next',
  'not_in_next'
]

def parseFromLogicalOp(sgLogicalOp):
  '''
  Parses a Shotgun logical operator and returns the search expression
  representation of it.

  Args:
    * (dict) sgLogicalOp:
      Shotgun formatted logical operator.
  '''

  try:
    op = ' %s ' % sgLogicalOp['logical_operator']

    comps = []

    for c in sgLogicalOp['conditions']:
      if c.has_key('logical_operator'):
        comps.append('(%s)' % parseFromLogicalOp(c))
      else:
        data = {
          'path': c['path'],
          'values': c['values']
        }

        relation = c['relation']

        if relation in LOG_SINGLES:
          data['values'] = repr(data['values'][0])

          exp = LOG_TO_ORM_LOOKUP[relation] % data

          comps.append(exp)
        elif relation in LOG_DOUBLES:
          data['value1'] = repr(data['values'][0])
          data['value2'] = repr(data['values'][1])

          exp = LOG_TO_ORM_LOOKUP[relation] % data

          comps.append(exp)
        else:
          exp = LOG_TO_ORM_LOOKUP[relation] % data

          comps.append(exp)

    return op.join(comps)
  except Exception, e:
    raise SgScriptError('error parsing logical operator: %s' % e)
