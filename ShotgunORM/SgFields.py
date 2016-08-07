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
  'SgFieldCheckbox',
  'SgFieldColor',
  'SgFieldColor2',
  'SgFieldDate',
  'SgFieldDateTime',
  'SgFieldEntity',
  'SgFieldEntityMulti',
  'SgFieldFloat',
  'SgFieldID',
  'SgFieldImage',
  'SgFieldInt',
  'SgFieldSelectionList',
  'SgFieldTagList',
  'SgFieldText',
  'SgFieldTimeCode',
  'SgFieldType',
  'SgFieldUrl'
]

# Python imports
import copy
import datetime
import os
import re
import threading
import time
import urllib2
import webbrowser

# This module imports
import ShotgunORM

class SgFieldCheckbox(ShotgunORM.SgField):
  '''
  Entity field that stores a bool value for a checkbox.
  '''

  def _fromFieldData(self, sgData):
    try:
      sgData = bool(sgData)
    except:
      raise TypeError('%s invalid value type "%s", expected a bool' % (self, type(sgData).__name__))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    try:
      sgData = bool(sgData)
    except:
      raise TypeError('%s invalid value type "%s", expected a bool' % (self, type(sgData).__name__))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldColor(ShotgunORM.SgField):
  '''
  Entity field that stores a list of 3 ints that represent a rgb color 0-255.

  Example: [128, 128, 128]
  '''

  REGEXP_COLOR = re.compile(r'(\d+,\d+,\d+)')

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if not result:
        self._value = None

      return result

    try:
      if not self.REGEXP_COLOR.match(sgData):
        raise ValueError('invalid value %s' % sgData)
    except Exception, e:
      ShotgunORM.LoggerField.error('%(field)s: %(error)s', {
        'field': self,
        'error': e
      })

      raise ValueError('%s invalid data from Shotgun "%s", expected a list of ints' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if not result:
        self._value = sgData

      return result

    try:
      if isinstance(sgData, str):
        if not self.REGEXP_COLOR.match(sgData):
          raise ValueError('invalid value %s' % sgData)
      else:
        if len(sgData != 3):
          raise ValueError('invalid value %s' % sgData)

        sgData = '%d,%d,%d' % (sgData[0], sgData[1], sgData[2])
    except:
      raise TypeError('%s invalid value "%s", expected a list of three ints' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _Value(self):
    if self._value == None:
      return None

    result = []

    for i in self._value.split(','):
      result.append(int(i))

    return result

class SgFieldColor2(ShotgunORM.SgField):
  '''
  Entity field that stores a list of 3 ints that represent a rgb color 0-255.

  Fix the color return value for Task and Phase Entities color field.

  Task and Phase Entities can have their color field set to a value that points
  to the color field of the pipeline step or project they belong to.

  Brilliant engineering to still call the return type "color" and not
  differentiate the two I know right?
  '''

  REGEXP_COLOR = re.compile(r'(\d+,\d+,\d+)')
  REGEXP_TASK_COLOR = re.compile(r'(\d+,\d+,\d+)|(pipeline_step)')
  REGEXP_PHASE_COLOR = re.compile(r'(\d+,\d+,\d+)|(project)')

  def __init__(self, name, label=None, sgFieldSchemaInfo=None, sgEntity=None):
    self._regexp = self.REGEXP_COLOR
    self._linkString = None
    self._linkField = None
    self._linkEntity = None

    super(SgFieldColor2, self).__init__(
      name,
      label=label,
      sgFieldSchemaInfo=sgFieldSchemaInfo,
      sgEntity=sgEntity
    )

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if not result:
        self._value = None

      return result

    if not self._regexp.match(sgData):
      raise ValueError('%s invalid color value "%s", expected format is "255,255,255" or "%s"' % (self, sgData, self._linkString))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _invalidate(self):
    super(SgFieldColor2, self)._invalidate()

    self._linkEntity = None

  def returnType(self):
    return self.RETURN_TYPE_COLOR2

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if isinstance(sgData, str):
      if not self._regexp.match(sgData):
        raise ValueError('%s invalid color value "%s", expected format is "255,255,255" or "%s"' % (self, sgData, self._linkString))
    else:
      if not isinstance(sgData, (tuple, list)):
        raise TypeError('%s invalid value type "%s", expected a list' % (self, type(sgData).__name__))

      if len(sgData) != 3:
        raise ValueError('%s list len is not 3' % self)

      newData = []

      try:
        sgData = '%d,%d,%d' % tuple(sgData)
      except:
        raise ValueError('%s invalid color values %s' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def linkField(self):
    '''
    Returns the link field this color field can possibly link to.
    '''

    return self._linkField

  def parentChanged(self):
    '''

    '''

    parent = self.parentEntity()

    if parent == None:
      return

    pType = parent.schemaInfo().name()

    self._linkEntity = None

    if pType == 'Task':
      self._regexp = self.REGEXP_TASK_COLOR
      self._linkString = 'pipeline_step'
      self._linkField = 'step'
    elif pType == 'Phase':
      self._regexp = self.REGEXP_PHASE_COLOR
      self._linkString = 'project'
      self._linkField= 'project'
    else:
      self._regexp = self.REGEXP_COLOR

  def value(self, linkEvaluate=True):
    '''
    Args:
      * (bool) linkEvaluate:
        When True and the color field is a link to another Entity's color field
        the value of the linked color field will be returned.

        If linkEvaluate is False a string may be returned instead of a list.
    '''

    result = super(SgFieldColor2, self).value()

    if result == None:
      return None

    if not linkEvaluate and result == self._linkString:
      return result

    parent = self.parentEntity()

    if parent == None:
      if result == self._linkString:
        return None

      newResult = []

      for i in result.split(','):
        newResult.append(int(i))

    if result == self._linkString:
      if self._linkEntity != None:
        return self._linkEntity['color']

      self._linkEntity = self.parentEntity().field(
        self._linkField
      ).value(['color'])

      if self._linkEntity == None:
        return None

      return self._linkEntity['color']
    else:
      newResult = []

      for i in result.split(','):
        newResult.append(int(i))

      return newResult

class SgFieldDate(ShotgunORM.SgField):
  '''
  Entity field that stores a date string

  Example: "1980-01-30".
  '''

  REGEXP = re.compile(r'^\d{4}-\d{2}-\d{2}')

  def _fromFieldData(self, sgData):
    if sgData != None:
      sgData = str(sgData)

      if not self.REGEXP.match(sgData):
        raise ValueError('%s invalid date string from Shotgun "%s"' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, (str, unicode)):
        raise TypeError('%s invalid type "%s", expected a string' % (self, type(sgData).__name__))

      sgData = str(sgData)

      if not self.REGEXP.match(sgData):
        raise ValueError('%s invalid date string "%s"' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldDateTime(ShotgunORM.SgField):
  '''
  Entity field that stores a python datetime object.
  '''

  def _fromFieldData(self, sgData):
    if sgData != None:
      sgData = datetime.datetime(*sgData.timetuple()[:6], tzinfo=sgData.tzinfo)

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, datetime.datetime):
        raise TypeError('%s invalid type "%s", expected a datetime obj' % (self, type(sgData).__name__))

      sgData = datetime.datetime(*sgData.timetuple()[:6], tzinfo=sgData.tzinfo)

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    result = self._value

    if result == None:
      return result

    return datetime.datetime(*result.timetuple()[:6], tzinfo=result.tzinfo)

  def _Value(self):
    return self._toFieldData()

class SgFieldEntity(ShotgunORM.SgField):
  '''
  Entity field that stores a link to another Entity.
  '''

  ##############################################################################
  #
  # IMPORTANT!!!!
  #
  # Any changes to _fromFieldData, _setValue, _toFieldData, value functions
  # should also be applied to the SgUserFieldAbstractEntity class.
  #
  ##############################################################################

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    try:
      newValue = copy.deepcopy(sgData)

      # This fixes the two Entities as their name field is only available when
      # returned as another Entities field value.
      if newValue['type'] in ['AppWelcome', 'Banner'] and sgData.has_key('name'):
          newValue['name'] = sgData['name']

    except Exception, e:
      ShotgunORM.LoggerField.error('%(field)s: %(error)s', {
        'field': self,
        'error': e
      })

      raise ValueError('%s invalid data from Shotgun "%s", expected a Shotgun formated Entity dict' % (self, sgData))

    if newValue == self._value:
      return False

    parent = self.parentEntity()

    self._value = newValue

    return True

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if not isinstance(sgData, ShotgunORM.SgEntity):
      raise TypeError('%s invalid value type "%s", expected a SgEntity' % (self, type(sgData).__name__))

    valueTypes = self.valueTypes()

    if valueTypes != None:
      if len(valueTypes) > 0:
        if not sgData.type in valueTypes:
          raise ValueError('not a valid value Entiy type: %s, valid=%s' % (sgData.type, valueTypes))

    if sgData['id'] == None:
      raise RuntimeError('can not set field value to a Entity that has not been created in Shotgun yet')

    parent = self.parentEntity()

    if parent == None:
      raise RuntimeError('field does not have a parent')

    connection = parent.connection()

    # Lord knows you shouldn't do this but if you build it people will try!
    if connection.url() != sgData.connection().url():
      raise ValueError('%s passed an Entity from another url' % self)

    if self._value == sgData:
      return False

    self._value = sgData.toEntityFieldData()

    return True

  def _toFieldData(self):
    if self._value == None:
      return None

    return {
      'id': self._value['id'],
      'type': self._value['type']
    }

  def value(self, sgSyncFields=None):
    '''
    Returns the fields value as a Entity object.

    Args:
      * (list) sgSyncFields:
        List of field names to populate the returned Entity with.
    '''

    value = super(SgFieldEntity, self).value()

    parent = self.parentEntity()

    if value == None or parent == None:
      return None

    connection = parent.connection()

    if isinstance(sgSyncFields, dict):
      sgSyncFields = sgSyncFields.get(value['type'], None)
    elif isinstance(sgSyncFields, str):
      sgSyncFields = [sgSyncFields]

    if sgSyncFields == None:
      sgSyncFields = connection.defaultEntityQueryFields(value['type'])

      if len(sgSyncFields) <= 0:
        sgSyncFields = None
    else:
      pullFields = set(sgSyncFields)

      extraFields = []

      if 'all' in pullFields:
        pullFields.remove('all')

        extraFields = parent.fieldNames()

        if 'default' in pullFields:
          pullFields.remove('default')
      elif 'default' in pullFields:
        pullFields.remove('default')

        extraFields = connection.defaultEntityQueryFields(value['type'])

      pullFields.update(extraFields)

      if len(pullFields) >= 1:
        sgSyncFields = list(pullFields)
      else:
        sgSyncFields = None

    result = connection._createEntity(
      value['type'],
      value,
      sgSyncFields=sgSyncFields
    )

    return result

class SgFieldEntityMulti(ShotgunORM.SgField):
  '''
  Entity field that stores a list of links to other Entities.

  Example: [Entity01, Entity02, ...]
  '''

  ##############################################################################
  #
  # IMPORTANT!!!!
  #
  # Any changes to _fromFieldData, _setValue, _toFieldData, value functions
  # should also be applied to the SgUserFieldAbstractMultiEntity class.
  #
  ##############################################################################

  def _fromFieldData(self, sgData):
    if isinstance(sgData, (tuple, set)):
      sgData = list(sgData)

    if sgData in [None, []]:
      result = self._value in [None, []]

      if result:
        self._value = self.defaultValue()

      return result

    newValue = []

    try:
      for i in sgData:
        e = {
          'type': i['type'],
          'id': i['id']
        }

        if e in newValue:
          continue

        # This fixes the two Entities as their name field is only available when
        # returned as another Entities field value.
        if e['type'] in ['AppWelcome', 'Banner'] and i.has_key('name'):
            e['name'] = i['name']

        newValue.append(e)
    except Exception, e:
      ShotgunORM.LoggerField.error('%(field)s: %(error)s', {
        'field': self,
        'error': e
      })

      raise ValueError('%s invalid data from Shotgun "%s", expected a Shotgun formated Entity dict' % (self, sgData))

    if self._value == newValue:
      return False

    self._value = newValue

    return True

  def _setValue(self, sgData):
    if isinstance(sgData, (tuple, set)):
      sgData = list(sgData)

    if sgData in [None, []]:
      result = self._value in [None, []]

      if result:
        self._value = self.defaultValue()

      return result

    if isinstance(sgData, ShotgunORM.SgEntity):
      sgData = [sgData]
    elif not isinstance(sgData, list):
      raise TypeError('%s invalid value type "%s", expected a SgEntity or list' % (self, type(sgData).__name__))
    else:
      for i in sgData:
        if not isinstance(i, ShotgunORM.SgEntity):
          raise TypeError('%s invalid value type "%s", expected a SgEntity' % (self, type(i).__name__))

    valueTypes = self.valueTypes()

    if valueTypes != None:
      if len(valueTypes) > 0:
        for i in sgData:
          if not i.type in valueTypes:
            raise ValueError('not a valid value type: %s, valid=%s' % (i.type, valueTypes))

    parent = self.parentEntity()

    newValue = []

    if parent == None:
      for i in sgData:
        if i['id'] == None:
          raise RuntimeError('can not set field value to a SgEntity that has not been created in Shotgun yet')

        edata = i.toEntityFieldData()

        if edata in newValue:
          continue

        newValue.append(edata)
    else:
      connection = parent.connection()


      for i in sgData:
        if i['id'] == None:
          raise RuntimeError('can not set field value to a SgEntity that has not been created in Shotgun yet')

        # Lord knows you shouldn't do this but if you build it people will try!
        if connection.url() != i.connection().url():
          raise ValueError('%s passed an Entity from another url' % self)

        edata = i.toEntityFieldData()

        if edata in newValue:
          continue

        newValue.append(edata)

    if self._value == newValue:
      return False

    self._value = newValue

    return True

  def _toFieldData(self):
    if self._value == None:
      return None

    result = []

    for i in self._value:
      result.append(dict(i))

    return result

  def value(self, sgSyncFields=None):
    '''
    Returns the fields value as a list of Entity objects.

    Args:
      * (dict) sgSyncFields:
        Dict of entity types and field names to populate the returned Entities
        with.
    '''

    result = super(SgFieldEntityMulti, self).value()

    if result in [None, []]:
      return []

    parent = self.parentEntity()

    if parent == None:
      return copy.deepcopy(result)

    connection = parent.connection()
    schema = connection.schema()

    tmp = []

    qEng = connection.queryEngine()

    qEng.block()

    try:
      for i in result:
        t = i['type']

        iSyncFields = None

        if sgSyncFields != None:
          if sgSyncFields.has_key(t):
            iFields = sgSyncFields[t]

            if iFields == None:
              iSyncFields = connection.defaultEntityQueryFields(t)

              if len(iSyncFields) <= 0:
                iSyncFields = None
            else:
              pullFields = []

              if isinstance(iFields, str):
                pullFields = set([iFields])
              else:
                pullFields = set(iFields)

              extraFields = []

              if 'all' in pullFields:
                pullFields.remove('all')

                extraFields = schema.entityInfo(t).fieldNames()

                if 'default' in pullFields:
                  pullFields.remove('default')
              elif 'default' in pullFields:
                pullFields.remove('default')

                extraFields = connection.defaultEntityQueryFields(t)

              pullFields.update(extraFields)

              if len(pullFields) >= 1:
                iSyncFields = list(pullFields)
              else:
                iSyncFields = None
          else:
            iSyncFields = connection.defaultEntityQueryFields(t)

            if len(iSyncFields) <= 0:
              iSyncFields = None
        else:
          iSyncFields = connection.defaultEntityQueryFields(t)

        entity = connection._createEntity(t, i, sgSyncFields=iSyncFields)

        tmp.append(entity)
    finally:
      qEng.unblock()

    return tmp

class SgFieldFloat(ShotgunORM.SgField):
  '''
  Entity field that stores a float.
  '''

  def _fromFieldData(self, sgData):
    if sgData != None:
      try:
        sgData = float(sgData)
      except:
        raise ValueError('%s invalid data from Shotgun "%s", expected a float' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData != None:
      try:
        sgData = float(sgData)
      except:
        raise TypeError('%s invalid value type "%s", expected a float' % (self, type(sgData).__name__))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldInt(ShotgunORM.SgField):
  '''
  Entity field that stores an integer.
  '''

  def _fromFieldData(self, sgData):
    if sgData != None:
      try:
        sgData = int(sgData)
      except:
        raise ValueError('%s invalid data from Shotgun "%s", expected a int' % (self, sgData))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData != None:
      try:
        sgData = int(sgData)
      except:
        raise TypeError('%s invalid value type "%s", expected a int' % (self, type(sgData).__name__))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldSelectionList(ShotgunORM.SgField):
  '''
  Entity field that stores a text string that is from a list selection.

  The field may contain a list of valid values which when the field is set are
  compared and an Exception thrown when the value is not a valid one.
  '''

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if not result:
        self._value = None

      return result

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def displayValue(self):
    '''
    Returns the display string of the selections value.

    If no display string exists then the selections value is returned instead.
    '''

    val = self.value()

    return self.schemaInfo().displayValues().get(
      val,
      val
    )

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if result:
        self._value = None

      return result

    if not isinstance(sgData, (str, unicode)):
      raise TypeError('%s invalid type "%s", expected a string' % (self, type(sgData).__name__))

    sgData = str(sgData)

    if self._value == sgData:
      return False

    validValues = self.validValues()

    if len(validValues) > 0:
      if not sgData in validValues:
        raise ValueError('%s invalid value "%s"' % (self, sgData))

    self._value = sgData

    return True

class SgFieldSerializable(ShotgunORM.SgField):
  '''
  Entity field that stores serializable data.
  '''

  def _fromFieldData(self, sgData):
    if sgData in [None, {}]:
      result = self._value in [None, {}]

      if result:
        self._value = None

      return result

    if not isinstance(sgData, (dict, list)):
      raise ValueError('%s invalid data from Shotgun "%s", expected a dict' % (self, sgData))

    if self._value == sgData:
      return False

    sgData = copy.deepcopy(sgData)

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value == sgData

      if result:
        self._value = None

      return result

    if not isinstance(sgData, (dict, list)):
      raise TypeError('%s invalid value type "%s", expected a dict' % (self, type(sgData).__name__))

    if self._value == sgData:
      return False

    sgData = copy.deepcopy(sgData)

    self._value = sgData

    return True

  def _toFieldData(self):
    if self._value == None:
      return None

    return copy.deepcopy(self._value)

  def _Value(self):
    return self._toFieldData()

class SgFieldSummary(ShotgunORM.SgField):
  '''
  Entity field that returns an Entity or list of Entities based on a search
  expression.

  Summary fields.
  '''

  DATE_REGEXP = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}) UTC')

  def __init__(self, name, label=None, sgFieldSchemaInfo=None, sgEntity=None):
    super(SgFieldSummary, self).__init__(
      name,
      label=label,
      sgFieldSchemaInfo=sgFieldSchemaInfo,
      sgEntity=sgEntity
    )

    self.__buildLock = threading.Lock()

    summaryInfo = self.schemaInfo().summaryInfo()

    if summaryInfo == None:
      raise RuntimeError('invalid field schema info for summary info')

    self._entityType = summaryInfo['entity_type']
    self._filtersRaw = summaryInfo['filters']
    self._summaryType = summaryInfo['summary_type']
    self._summaryField = summaryInfo['summary_field']
    self._summaryValue = summaryInfo['summary_value']

    self._searchFilter = None

  def _buildLogicalOp(self, conditions, info):
    '''
    Builds the logical operator search pattern and returns it.
    '''

    result = []

    parent = self.parentEntity()
    connection = parent.connection()

    for c in conditions:
      if c.has_key('logical_operator'):
        logicalOp = {
          'conditions': self._buildLogicalOp(c['conditions'], info),
          'logical_operator': c['logical_operator']
        }

        result.append(logicalOp)
      else:
        newValues = []

        cInfo = info.fieldInfo(c['path'])
        cType = cInfo.returnType()

        ########################################################################
        #
        # Date and Date Time fields
        #
        ########################################################################
        if cType in [ShotgunORM.SgField.RETURN_TYPE_DATE, ShotgunORM.SgField.RETURN_TYPE_DATE_TIME]:
          # http://stackoverflow.com/a/13287083
          def utc_to_local(utc_dt):
              # get integer timestamp to avoid precision lost
              timestamp = calendar.timegm(utc_dt.timetuple())
              local_dt = datetime.fromtimestamp(timestamp)
              assert utc_dt.resolution >= timedelta(microseconds=1)
              return local_dt.replace(microsecond=utc_dt.microsecond)

          for v in c['values']:
            if isinstance(v, dict):
              if v.has_key('relative_day'):
                time = datetime.time(*v['time'])

                date = datetime.date.today()

                rd = v['relative_day']

                if rd == 'tomorrow':
                  date = date.replace(day=date.day + 1)
                elif rd == 'yesterday':
                  date = date.replace(day=date.day - 1)

                dt = datetime.datetime.combine(date, time)

                # Relative day calcs use utc time!
                dt.replace(tzinfo=None)

                newValues.append(dt)
              else:
                newValues.append(v)
            elif isinstance(v, str):
              search = DATE_REGEXP.match(v)

              if search:
                time = datetime.time(search.group(4), search.group(5), search.group(6))
                date = datetime.date(search.group(1), search.group(2), search.group(3))

                dt = datetime.datetime.combine(date, time)

                dt.replace(tzinfo=None)

                newValues.append(utc_to_local(dt))
              else:
                newValues.append(v)

        ########################################################################
        #
        # Entity and Multi-Entity fields
        #
        ########################################################################
        elif cType in [ShotgunORM.SgField.RETURN_TYPE_ENTITY, ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY]:
          for v in c['values']:
            if v['name'] == 'Current %s' % parent.type:
              newValues.append(parent.toEntityFieldData())
            elif v['name'] == 'Me':
              login = os.getenv('USERNAME')
              user = connection.findOne('HumanUser', [['login', 'is', login]], ['login'])

              if user == None:
                raise RuntimError('summary field unable to find user "%s" in Shotgun' % login)

              newValues.append(user.toEntityFieldData())
            else:
              newValues.append(v)
        else:
          # Do nothing
          newValues = c['values']

        c['values'] = newValues

        del c['active']

        result.append(c)

    return result

  def _buildSearchFilter(self):
    '''

    '''

    opsRaw = copy.deepcopy(self._filtersRaw)

    logicalOps = {
      'conditions': self._buildLogicalOp(
        opsRaw['conditions'],
        self.parentEntity().connection().schema().entityInfo(self.entityType())
      ),
      'logical_operator': opsRaw['logical_operator']
    }

    self._searchFilter = logicalOps

  def _fromFieldData(self, sgData):
    '''
    Always return False for summary fields, they can not be set.
    '''

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    result = self._value

    if result == None:
      return None

    if isinstance(result, dict):
      return copy.deepcopy(result)

    return result

  def entityType(self):
    '''
    Returns the type of Entity the summary field will return.
    '''

    return self._entityType

  def hasCommit(self):
    '''
    Always returns False for summary fields.
    '''

    return False

  def _invalidate(self):
    '''
    Deletes the search filter so its built again.
    '''

    self._searchFilter = None

  def isEditable(self):
    '''
    Always return False for summary fields.
    '''

    return False

  def isQueryable(self):
    '''
    Even though summary fields can be queried from Shotgun return False.
    '''

    return False

  def setHasCommit(self, valid):
    '''
    Summary fields can't be committed, always returns False.
    '''

    return False

  def setHasSyncUpdate(self, valid):
    '''
    Summary fields cant be queried so thus they can not be background pulled.

    Always returns False.
    '''

    return False

  def _setValue(self, value):
    '''
    Always return False for summary fields, they can not be set.
    '''

    return False

  def _valueSg(self):
    parent = self.parentEntity()

    if parent == None or not parent.exists():
      return None

    connection = parent.connection()

    with self.__buildLock:
      if self._searchFilter == None:
        self._buildSearchFilter()

    searchExp = self._searchFilter

    result = None

    ############################################################################
    #
    # Single record
    #
    ############################################################################
    if self._summaryType == 'single_record':
      order = [
        {
          'field_name': self._summaryValue['column'],
          'direction': self._summaryValue['direction']
        }
      ]

      result = connection._sg_find_one(self.entityType(), searchExp, order=order)

    ############################################################################
    #
    # Status percentage and list
    #
    ############################################################################
    elif self._summaryType.startswith('status_'):
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if self._summaryType == 'status_percentage':
        if len(sgSearch) <= 0:
          result = 0
        else:
          validCount = 0

          for e in sgSearch:
            value = e.field(self._summaryField).value()

            if value == self._summaryValue:
              validCount += 1

          if validCount <= 0:
            result = 0.0
          else:
            result = float(validCount) / len(sgSearch)
      elif self._summaryType == 'status_list':
        if len(sgSearch) <= 0:
          result = 'ip'
        else:
          value = sgSearch[0].field(self._summaryField).value()

          for e in sgSearch[1:]:
            v = e.field(self._summaryField).value()

            if v != value:
              # I have no clue why Shotgun always defaults this result to ip
              # but whatevs yo.
              value = 'ip'

              break

          result = value

    ############################################################################
    #
    # Record count
    #
    ############################################################################
    elif self._summaryType == 'record_count':
      # Dont use the orm for this search, waste to build the classes when all
      # we are doing is getting a len on the search result.
      sgSearch = connection._sg_find(self.entityType(), searchExp)

      result = len(sgSearch)
    elif self._summaryType == 'count':
      searchExp = {
        'conditions': [
          searchExp,
          {
            #'active': 'true',
            'path': self._summaryField,
            'relation': 'is_not',
            'values': [None]
          }
        ],
        'logical_operator': 'and'
      }

      # Dont use the orm for this search, waste to build the classes when all
      # we are doing is getting a len on the search result.
      sgSearch = connection._sg_find(self.entityType(), searchExp, fields=[])

      result = len(sgSearch)

    ############################################################################
    #
    # Sum
    #
    ############################################################################
    elif self._summaryType == 'sum':
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        result = 0
      else:
        value = 0

        for e in sgSearch:
          v = e.field(self._summaryField).value()

          if v != None:
            value += v

        result = value

    ############################################################################
    #
    # Min
    #
    ############################################################################
    elif self._summaryType == 'min':
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        result = None
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value = min(v, value)

        result = value

    ############################################################################
    #
    # Max
    #
    ############################################################################
    elif self._summaryType == 'max':
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        result = None
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value = max(v, value)

        result = value

    ############################################################################
    #
    # Average
    #
    ############################################################################
    elif self._summaryType == 'avg':
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        result = 0
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value += v

        value = float(value) / len(sgSearch)

        result = value

    ############################################################################
    #
    # Percentage
    #
    ############################################################################
    elif self._summaryType == 'percentage':
      sgSearch = connection.find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        result = 0
      else:
        value = 0

        for e in sgSearch:
          if e.field(self._summaryField).value() == self._summaryValue:
            value += 1

        if value >= 1:
          value = float(value) / len(sgSearch)

        result = value

    return result

  def _Value(self):
    if self._value == None:
      return None

    if self._summaryType == 'single_record':
      parent = self.parentEntity()

      if parent == None:
        return copy.deepcopy(self._value)

      connection = parent.connection()

      return connection._createEntity(self._value['type'], self._value)

    return copy.deepcopy(self._value)

class SgFieldTagList(ShotgunORM.SgField):
  '''
  Entity field that stores a list of strings.

  The field may contain a list of valid values which when the field is set are
  compared and an Exception thrown when the value is not a valid one.
  '''

  def _fromFieldData(self, sgData):
    if isinstance(sgData, (tuple, set)):
      sgData = list(sgData)

    if sgData in [None, []]:
      result = self._value in [None, []]

      if result:
        self._value = self.defaultValue()

      return result

    for i in sgData:
      if not isinstance(i, str):
        raise TypeError('%s invalid type "%s" in value "%s", expected a string' % (self, type(i).__name__, sgData))

    sgData = list(set(sgData))

    validValues = self.validValues()

    if len(validValues) > 0:
      for i in sgData:
        if not i in validValues:
          ValueError('%s invalid value "%s", valid %s' % (self, i, validValues))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if isinstance(sgData, (tuple, set)):
      sgData = list(sgData)

    if sgData in [None, []]:
      result = self._value in [None, []]

      if result:
        self._value = self.defaultValue()

      return result

    for i in sgData:
      if not isinstance(i, str):
        raise TypeError('%s invalid type "%s" in value "%s", expected a string' % (self, type(i).__name__, sgData))

    sgData = list(set(sgData))

    validValues = self.validValues()

    if len(validValues) > 0:
      for i in sgData:
        if not i in validValues:
          ValueError('%s invalid value "%s", valid %s' % (self, i, validValues))

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    result = self._value

    if result == None:
      return None

    return list(result)

  def _Value(self):
    return self._toFieldData()

class SgFieldText(ShotgunORM.SgField):
  '''
  Entity field that stores a str.
  '''

  def _fromFieldData(self, sgData):
    if self._value == sgData:
      return False

    self._value = str(sgData)

    return True

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, (str, unicode)):
        raise TypeError('%s invalid value type "%s", expected a str' % (self, type(sgData).__name__))

      sgData = str(sgData)

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldTimeCode(ShotgunORM.SgField):
  '''
  Entity field that stores timecode.
  '''

  def _fromFieldData(self, sgData):
    if sgData != None:
      try:
        sgData = int(sgData)
      except:
        raise ValueError('%s invalid data from Shotgun "%s", expected a int' % (self, sgData))

      if abs(sgData) > 86400000:
        ShotgunORM.LoggerField.warn(
          '%(sgField)s._fromFieldData(sgData) timecode value from shotgun is '
          'greater than the milliseconds in a day, value=%(value)s',
          {
            'sgField': self,
            'value': sgData
          }
        )

    if self._value == sgData:
      return False

    self._value = sgData

    return True

  def _setValue(self, sgData):
    if sgData != None:
      try:
        sgData = int(sgData)
      except:
        raise TypeError('%s invalid value type "%s", expected a int' % (self, type(sgData).__name__))

      if abs(sgData) > 86400000:
        raise ValueError('timecode value can not be greater than 86400000')

    if self._value == sgData:
      return False

    self._value = sgData

    return True

class SgFieldImage(SgFieldText):
  '''
  See SgFieldText.
  '''

  REGEXP_EXPIRETIME = re.compile(r'\?(?:AWS)?AccessKeyId=.*&Expires=(\d+)&Signature=')

  def __init__(self, name, label=None, sgFieldSchemaInfo=None, sgEntity=None):
    super(SgFieldImage, self).__init__(
      name,
      label=label,
      sgFieldSchemaInfo=sgFieldSchemaInfo,
      sgEntity=sgEntity
    )

    self.__expireTime = 0

  def _invalidate(self):
    self.__expireTime = 0

  def _validate(self, forReal=False):
    result = super(SgFieldImage, self)._validate(forReal)

    if result and forReal and self._value != None:
      search = self.REGEXP_EXPIRETIME.search(self._value)

      if search == None:
        ShotgunORM.LoggerField.warn(
          '%(sgField)s._validate() unable to find image expire time in %(image)s',
          {
            'sgField': self,
            'image': self._value
          }
        )
      else:
        self.__expireTime = int(search.group(1))

    return result

  def downloadThumbnail(self, path):
    '''
    Downloads the image to the specified path.
    '''

    url = self.value()

    if url == None or url == '':
      raise ValueError('%s value is empty' % self)

    if os.path.exists(path) and os.path.isdir(path):
      raise OSError('output path "%s" is a directory' % path)

    try:
      data = urllib2.urlopen(url)

      f = open(path, 'w')

      f.write(data.read())

      f.close()
    except Exception, e:
      ShotgunORM.LoggerField.error('%(field)s: %(error)s', {
        'field': self,
        'error': e
      })

      raise RuntimeError(
        '%s an error occured while downloading the file, %s' % (
          self,
          e

        )
      )

    return True

  def filename(self):
    '''
    Returns the filename of the image url.

    Returns an empty string if the field is not set.
    '''

    img = self.value()

    if img == None:
      return ''

    search = self.REGEXP_EXPIRETIME.search(img)

    if search != None:
      return img[:search.span(0)[0]].rsplit('/', 1)[-1]

    return img.replace('\\', '/').rsplit('/', 1)[-1]

  def isCacheable(self):
    '''
    Returns False.

    Image fields are not cachable since they have expire times.
    '''

    return False

  def isLinkExpired(self):
    '''
    Returns True if the image fields value has expired and can no longer be
    downloaded.
    '''

    return (
      self.__expireTime != 0 and
      time.time() >= self.__expireTime
    )

  def isValid(self):
    if super(SgFieldImage, self).isValid():
      return not self.isLinkExpired()

    return False

  def linkExpireTime(self):
    '''
    Returns the links expire time.

    When the field has not yet validated returns 0.
    '''

    return self.__expireTime

  def openInBrowser(self):
    '''
    Opens the image in a web-browser
    '''

    url = self.value()

    if url != None and url != '':
      webbrowser.open(url)

  def secondsTillExpired(self):
    '''
    Returns the number of seconds till the link is expired.
    '''

    if self.__expireTime == 0:
      return -1
    else:
      return self.__expireTime - time.time()

  def uploadThumbnail(self, path):
    '''
    Uploads the specified image file and sets it as the Entities thumbnail.

    Returns the Attachment id.
    '''

    parent = self.parentEntity()

    if not parent.exists():
      raise RuntimeError('parent entity does not exist')

    with self:
      if self.hasCommit():
        raise RuntimeError('can not upload a new thumbnail while the image field has an un-commited update')

      parent = self.parentEntity()

      if parent == None or not parent.exist():
        raise RuntimeError('parent entity does not exists')

      sgconnection = parent.connection().connection()

      with ShotgunORM.SHOTGUN_API_LOCK:
        sgResult = sgconnection.upload_thumbnail(parent.type, parent['id'], path)

      parent.sync([self.name()])

      return sgResult

  def uploadFilmstripThumbnail(self, path):
    '''
    Uploads the specified image file and sets it as the Entities flimstrip
    thumbnail.

    Returns the Attachment id.

    Note:
    This function is only valid for Version Entities.
    '''

    with self:
      if self.hasCommit():
        raise RuntimeError('can not upload a new thumbnail while the image field has an un-commited update')

      parent = self.parentEntity()

      if parent == None or not parent.exist():
        raise RuntimeError('parent entity does not exists')

      if not parent.type == 'Version':
        raise RuntimeError('only valid on Version Entities')

      sgconnection = parent.connection().connection()

      sgResult = sgconnection.upload_filmstrip_thumbnail(parent.type, parent['id'], path)

      parent.sync([self.name()])

      return sgResult

class SgFieldUrl(ShotgunORM.SgField):
  '''
  Entity field that stores a url.

  Example URL: {
    'content_type': 'image/jpeg',
    'link_type': 'upload',
    'name': 'bob.jpg',
    'url': 'http://www.owned.com/bob.jpg'
  }

  Example Local: {
    'content_type': 'image/jpeg',
    'link_type': 'local',
    'name': 'bob.jpg',
    'local_storage': 'c:/temp/bob.jpg'
  }
  '''

  REGEXP_EXPIRETIME = re.compile(r'\?(?:AWS)?AccessKeyId=.*&Expires=(\d+)&Signature=')

  def __init__(self, name, label=None, sgFieldSchemaInfo=None, sgEntity=None):
    super(SgFieldUrl, self).__init__(
      name,
      label=label,
      sgFieldSchemaInfo=sgFieldSchemaInfo,
      sgEntity=sgEntity
    )

    self.__expireTime = 0

  def _invalidate(self):
    self.__expireTime = 0

  def _fromFieldData(self, sgData):
    result = {}

    if sgData == None:
      result = self._value == None

      if not result:
        self._value = None

      return result

    if not isinstance(sgData, dict):
      raise TypeError('%s invalid sgData "%s", expected a dict or string' % (self, sgData))

    try:
      result['link_type'] = sgData['link_type'].lower()

      if result['link_type'] in ['upload', 'web']:
        result['url'] = sgData['url']
      else:
        result['id'] = sgData['id']
        result['local_path'] = sgData['local_path']
        result['local_path_linux'] = sgData['local_path_linux']
        result['local_path_mac'] = sgData['local_path_mac']
        result['local_path_windows'] = sgData['local_path_windows']
        result['local_storage'] = sgData['local_storage']
        result['type'] = sgData['type']

      result['name'] = sgData['name']
      result['content_type'] = sgData.get('content_type', None)
    except Exception, e:
      ShotgunORM.LoggerField.warn(e)

      raise TypeError('%s invalid sgData dict "%s"' % (self, sgData))

    if not result['link_type'] in ['local', 'upload', 'web']:
      raise ValueError('%s invalid link_type "%s"' % (self, result['link_type']))

    if self._value == result:
      return False

    self._value = result

    return True

  def isLinkExpired(self):
    '''
    Returns True if the url fields value has expired and can no longer be
    downloaded.
    '''

    return (
      self.__expireTime != 0 and
      time.time() >= self.__expireTime
    )

  def isValid(self):
    if super(SgFieldUrl, self).isValid():
      return not self.isLinkExpired()

    return False

  def linkExpireTime(self):
    '''
    Returns the links expire time.

    When the field has not yet validated returns 0.
    '''

    return self.__expireTime

  def secondsTillExpired(self):
    '''
    Returns the number of seconds till the link is expired.
    '''

    if self.__expireTime == 0:
      return -1
    else:
      return self.__expireTime - time.time()

  def setValue(self, sgData):
    return self.fromFieldData(sgData)

  def _toFieldData(self):
    if self._value == None:
      return None

    return copy.deepcopy(self._value)

  def _validate(self, forReal=False):
    result = super(SgFieldUrl, self)._validate(forReal)

    if forReal and self._value != None:
      if self._value['link_type'] in ['url', 'upload']:
        search = self.REGEXP_EXPIRETIME.search(self._value['url'])

        if search == None:
          ShotgunORM.LoggerField.warn(
            '%(sgField)s._validate() unable to find url expire time in %(url)s',
            {
              'sgField': self,
              'url': self._value
            }
          )
        else:
          self.__expireTime = int(search.group(1))

    return result

  def _Value(self):
    return self._toFieldData()

  def url(self, openInBrowser=False):
    '''
    Returns the url value.

    When the arg "openInBrowser" is set to True then the returned URL will
    also be opened in the operating systems default web-browser.
    '''

    data = self.value()

    result = ''

    if data == None:
      result = ''
    else:
      try:
        result = data['url']
      except:
        pass

    if openInBrowser:
      webbrowser.open(url)

    return result

  def urlName(self):
    '''
    Returns the url filename.
    '''

    data = self.value()

    if data == None:
      return ''

    return data['name']

  def urlType(self):
    '''
    Returns the Shotgun url type.

    Valid return value are None, "local", "url", "upload".
    '''

    data = self.value()

    if data == None:
      return None

    return data['link_type']

# Register the fields.
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_CHECKBOX, SgFieldCheckbox)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_COLOR, SgFieldColor)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_COLOR2, SgFieldColor2)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_DATE, SgFieldDate)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_DATE_TIME, SgFieldDateTime)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_ENTITY, SgFieldEntity)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_FLOAT, SgFieldFloat)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_IMAGE, SgFieldImage)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_INT, SgFieldInt)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_LIST, SgFieldSelectionList)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_MULTI_ENTITY, SgFieldEntityMulti)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_SERIALIZABLE, SgFieldSerializable)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_STATUS_LIST, SgFieldSelectionList)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_SUMMARY, SgFieldSummary)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_TAG_LIST, SgFieldTagList)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_TEXT, SgFieldText)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_TIMECODE, SgFieldTimeCode)
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_URL, SgFieldUrl)

################################################################################
#
# Custom fields
#
################################################################################

class SgFieldID(SgFieldInt):
  '''
  Field that returns the parent Entities Type.
  '''

  # Do not allow the field to lock, no point in it.
  def __enter__(self):
    pass

  def __exit__(self, exc_type, exc_value, traceback):
    return False

  def __init__(self, sgFieldSchemaInfo, sgEntity):
    super(SgFieldID, self).__init__(
      'id', 'id', sgFieldSchemaInfo, sgEntity
    )

    super(SgFieldID, self).setValid(True)

  def invalidate(self, force=True):
    '''
    Does nothing for ID fields.
    '''

    return False

  def isCacheable(self):
    '''
    Always returns False for ID fields.
    '''

    return False

  def setHasSyncUpdate(self, valid):
    '''
    Always returns False for ID fields.
    '''

    return False

  def setValid(self, valid):
    '''
    Always returns False for ID fields.
    '''

    return False

  def setValueFromShotgun(self):
    '''
    Always returns False for ID fields.
    '''

    return False

  def validate(self, forReal=False, force=False):
    '''
    Always returns False for ID fields.
    '''

    return False

  def value(self):
    '''
    Returns the value of the ID field.
    '''

    return self._value

  def _valueSg(self):
    '''
    Returns the value of the ID field.

    For ID fields this will never query Shotgun.
    '''

    return self._value

class SgFieldType(SgFieldText):
  '''
  Field that returns the parent Entities Type.
  '''

  # Do not allow the field to lock, no point in it.
  def __enter__(self):
    pass

  def __exit__(self, exc_type, exc_value, traceback):
    return False

  def __init__(self, sgFieldSchemaInfo, sgEntity):
    super(SgFieldType, self).__init__(
      'type', 'type', sgFieldSchemaInfo, sgEntity
    )

    super(SgFieldType, self).setValid(True)

  def invalidate(self, force=False):
    '''
    Always returns False for Type fields.
    '''

    return False

  def isCacheable(self):
    '''
    Always returns False for Type fields.
    '''

    return False

  def setHasSyncUpdate(self, valid):
    '''
    Always returns False for Type fields.
    '''

    return False

  def setValid(self, valid):
    '''
    Always returns False for Type fields.
    '''

    return False

  def setValueFromShotgun(self):
    '''
    Always returns False for Type fields.
    '''

    return False

  def validate(self, forReal=False, force=False):
    '''
    Always returns False for Type fields.
    '''

    return False

  def value(self):
    '''
    Returns the Entity type the field belongs to.
    '''

    return self._value

  def _valueSg(self):
    '''
    Returns the Entity type the field belongs to.

    For Type fields this will never query Shotgun.
    '''

    return self._value
