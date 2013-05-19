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
  'SgFieldImage',
  'SgFieldInt',
  'SgFieldSelectionList',
  'SgFieldTagList',
  'SgFieldText',
  'SgFieldUrl'
]

# Python imports
import copy
import datetime
import os
import re
import urllib2
import webbrowser

# This module imports
import ShotgunORM

class SgFieldCheckbox(ShotgunORM.SgField):
  '''
  Entity field that stores a bool value for a checkbox.
  '''

  def _setValue(self, sgData):
    try:
      sgData = bool(sgData)
    except:
      raise TypeError('%s invalid value type "%s", expected a bool' % (self.__repr__(), type(sgData).__name__))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    return self._value

class SgFieldColor(ShotgunORM.SgField):
  '''
  Entity field that stores a list of 3 ints that represent a rgb color 0-255.

  Example: [128, 128, 128]
  '''

  def _setValue(self, sgData):
    if sgData == self._value:
      return False

    if sgData != None:
      try:
        if len(sgData) != 3:
          raise RuntimeError('')

        sgData = [int(sgData[0]), int(sgData[1]), int(sgData[2])]
      except:
        raise TypeError('%s invalid value "%s", expected a list of three ints' % (self.__repr__(), sgData))

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    try:
      if sgData != None:
        sgData = sgData.split(',')

        if len(sgData) != 3:
          raise RuntimeError('')

        sgData = [int(sgData[0]), int(sgData[1]), int(sgData[2])]

      if sgData == self._value:
        return False

      self._value = sgData

      return True
    except Exception, e:
      ShotgunORM.LoggerEntityField.error(e)

      raise ValueError('%s invalid data from Shotgun "%s", expected a list of ints' % (self.__repr__(), sgData))

  def _toFieldData(self):
    if self._value == None:
      return None

    return '%d,%d,%d' % (self._value[0], self._value[1], self._value[2])

class SgFieldColor2(ShotgunORM.SgField):
  '''
  Entity field that stores a list of 3 ints that represent a rgb color 0-255.

  Fix the color return value for Task and Phase Entities color field.

  Task and Phase Entities can have their color field set to a value that points
  to the color field of the pipeline step or project they belong to.

  Brilliant engineering to still call the return type "color" and not
  differentiate the two I know right?
  '''

  REGEXP_TASK = re.compile(r'(\d+,\d+,\d+)|(pipeline_step)')
  REGEXP_PHASE = re.compile(r'(\d+,\d+,\d+)|(project)')

  def __init__(self, parentEntity, fieldInfo):
    super(SgFieldColor2, self).__init__(parentEntity, fieldInfo)

    if parentEntity.type == 'Task':
      self._regexp = self.REGEXP_TASK
      self._linkString = 'pipeline_step'
      self._linkField = 'step'
    else:
      self._regexp = self.REGEXP_PHASE
      self._linkString = 'project'
      self._linkField= 'project'

  def value(self):
    '''
    Returns the value of the color field as a list of ints.

    When the color field is set to "pipeline_step" then the value of the color
    field on the Pipeline step is returned.
    '''

    parent = self.parentEntity()

    parent._lock()

    try:
      parent._fetch([self.name(), self._linkField])

      if self._value == None:
        return None

      if self._value == self._linkString:
        try:
          return self.parentEntity()[self._linkField]['color']
        except:
          return None
      else:
        s = self._value.split(',')

        return [int(s[0]), int(s[1]), int(s[2])]
    except:
      raise
    finally:
      parent._release()

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if isinstance(sgData, str):
      if not self._regexp.match(sgData):
        raise ValueError('%s invalid color value "%s", expected format is "255,255,255" or "%s"' % (self.__repr__(), sgData, self._linkString))
    else:
      if not isinstance(sgData, (tuple, list)):
        raise TypeError('%s invalid value type "%s", expected a list' % (self.__repr__(), type(sgData).__name__))

      if len(sgData) != 3:
        raise ValueError('%s list len is not 3' % self.__repr__())

      newData = []

      try:
        sgData = '%d,%d,%d' % tuple(sgData)
      except:
        raise ValueError('%s invalid color values %s' % (self.__repr__(), sgData))

    # Link the field if its the same as the link fields color.
    # Lame as hell to support this bs but alas I digress :(.
    try:
      if sgData == self.parentEntity()[self._linkField]['color']:
        sgData = self._linkString
    except:
      pass

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value == sgData

      self._value = None

      return result

    if sgData == self._value:
      return False

    self._value = sgData

  def _toFieldData(self):
    return self._value

class SgFieldDate(ShotgunORM.SgField):
  '''
  Entity field that stores a date string

  Example: "1980-01-30".
  '''

  REGEXP = re.compile(r'^\d{4}-\d{2}-\d{2}')

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, (str, unicode)):
        raise TypeError('%s invalid type "%s", expected a string' % (self.__repr__(), type(sgData).__name__))

      sgData = str(sgData)

      if not self.REGEXP.match(sgData):
        raise ValueError('%s invalid date string "%s"' % (self.__repr__(), sgData))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData != None:
      sgData = str(sgData)

      if not self.REGEXP.match(sgData):
        raise ValueError('%s invalid date string from Shotgun "%s"' % (self.__repr__(), sgData))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    return self._value

class SgFieldDateTime(ShotgunORM.SgField):
  '''
  Entity field that stores a python datetime object.
  '''

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, datetime.datetime):
        raise TypeError('%s invalid type "%s", expected a datetime obj' % (self.__repr__(), type(sgData).__name__))

      sgData = datetime.datetime(*sgData.timetuple()[:6], tzinfo=sgData.tzinfo)

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData != None:
      sgData = datetime.datetime(*sgData.timetuple()[:6], tzinfo=sgData.tzinfo)

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    result = self._value

    if result == None:
      return result

    return datetime.datetime(*result.timetuple()[:6], tzinfo=result.tzinfo)

class SgFieldEntity(ShotgunORM.SgField):
  '''
  Entity field that stores a link to another Entity.
  '''

  def value(self):
    result = super(SgFieldEntity, self).value()

    if result == None:
      return None

    session = self.parentEntity().session()

    return session._createEntity(
      result['type'],
      result,
      list(session.connection().defaultEntityQueryFields(result['type']))
    )

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if not isinstance(sgData, ShotgunORM.SgEntity):
      raise TypeError('%s invalid value type "%s", expected a SgEntity' % (self.__repr__(), type(sgData).__name__))

    valueTypes = self.valueTypes()

    if valueTypes != None:
      if len(valueTypes) > 0:
        if not sgData.type in valueTypes:
          raise ValueError('not a valid value Entiy type: %s, valid=%s' % (sgData.type, valueTypes))

    if sgData['id'] == None:
      raise RuntimeError('can not set field value to a Entity that has not been created in Shotgun yet')

    parent = self.parentEntity()
    session = parent.session()
    connection = session.connection()

    # Lord knows you shouldn't do this but if you build it people will try!
    if connection.url() != sgData.session().connection().url():
      raise ValueError('%s passed an Entity from another url' % self.__repr__())

    newValue = sgData.toEntityFieldData()

    if newValue == self._value:
      return False

    self._value = newValue

    return True

  def _fromFieldData(self, sgData):
    # Dont check for valid value types since this function is only given data
    # straight from the Shotgun db.  Fail on Shotguns part if they should ever
    # pass you something that is not a valid value type.

    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    try:
      newValue = {
        'type': sgData['type'],
        'id': sgData['id']
      }
    except Exception, e:
      ShotgunORM.LoggerEntityField.error(e)

      raise ValueError('%s invalid data from Shotgun "%s", expected a Shotgun formated Entity dict' % (self.__repr__(), sgData))

    if newValue == self._value:
      return False

    self._value = newValue

    return True

  def _toFieldData(self):
    if self._value == None:
      return None

    return dict(self._value)

class SgFieldEntityMulti(ShotgunORM.SgField):
  '''
  Entity field that stores a list of links to other Entities.

  Example: [Entity01, Entity02, ...]
  '''

  def value(self):
    value = super(SgFieldEntityMulti, self).value()

    if value == None:
      return None

    session = self.parentEntity().session()

    result = session._createEntities(value)

    return result

  def _setValue(self, sgData):
    if sgData == None or len(sgData) <= 0:
      result = self._value != None and self._value != []

      self._value = []

      return result

    if isinstance(sgData, ShotgunORM.SgEntity):
      sgData = [sgData]
    elif not isinstance(sgData, list):
      raise TypeError('%s invalid value type "%s", expected a SgEntity or list' % (self.__repr__(), type(sgData).__name__))
    else:
      for i in sgData:
        if not isinstance(i, ShotgunORM.SgEntity):
          raise TypeError('%s invalid value type "%s", expected a SgEntity' % (self.__repr__(), type(i).__name__))

    valueTypes = self.valueTypes()

    if valueTypes != None:
      if len(valueTypes) > 0:
        for i in sgData:
          if not i.type in valueTypes:
            raise ValueError('not a valid value type: %s, valid=%s' % (i.type, valueTypes))

    parent = self.parentEntity()
    session = parent.session()
    connection = session.connection()

    newValue = []

    for i in sgData:
      if i['id'] == None:
        raise RuntimeError('can not set field value to a SgEntity that has not been created in Shotgun yet')

      # Lord knows you shouldn't do this but if you build it people will try!
      if connection.url() != i.session().connection().url():
        raise ValueError('%s passed an Entity from another url' % self.__repr__())

      newValue.append(i.toEntityFieldData())

    if self._value != None:
      if set(newValue) == set(self._value):
        return False

    self._value = newValue

    return True

  def _fromFieldData(self, sgData):
    # Dont check for valid value types since this function is only given data
    # straight from the Shotgun db.  Fail on Shotguns part if they should ever
    # pass you something that is not a valid value type.

    if sgData == None or len(sgData) <= 0:
      result = self._value != None and self._value != []

      self._value = []

      return result

    parent = self.parentEntity()
    session = parent.session()

    newValue = []

    try:
      for i in sgData:
        e = {
          'type': i['type'],
          'id': i['id']
        }

        newValue.append(e)
    except Exception, e:
      ShotgunORM.LoggerEntityField.error(e)

      raise ValueError('%s invalid data from Shotgun "%s", expected a Shotgun formated Entity dict' % (self.__repr__(), sgData))

    if self._value != None and len(self._value) >= 1:
      if set(self._value) == set(newValue):
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

class SgFieldFloat(ShotgunORM.SgField):
  '''
  Entity field that stores a float.
  '''

  def _setValue(self, sgData):
    if sgData != None:
      try:
        sgData = float(sgData)
      except:
        raise TypeError('%s invalid value type "%s", expected a float' % (self.__repr__(), type(sgData).__name__))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData != None:
      try:
        sgData = float(sgData)
      except:
        raise ValueError('%s invalid data from Shotgun "%s", expected a float' % (self.__repr__(), sgData))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    return self._value

class SgFieldInt(ShotgunORM.SgField):
  '''
  Entity field that stores an integer.
  '''

  def _setValue(self, sgData):
    if sgData != None and sgData != '':
      try:
        sgData = int(sgData)
      except:
        raise TypeError('%s invalid value type "%s", expected a int' % (self.__repr__(), type(sgData).__name__))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData != None and sgData != '':
      try:
        sgData = int(sgData)
      except:
        raise ValueError('%s invalid data from Shotgun "%s", expected a int' % (self.__repr__(), sgData))

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    return self._value

class SgFieldSelectionList(ShotgunORM.SgField):
  '''
  Entity field that stores a text string that is from a list selection.

  The field may contain a list of valid values which when the field is set are
  compared and an Exception thrown when the value is not a valid one.
  '''

  def _setValue(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if not isinstance(sgData, (str, unicode)):
      raise TypeError('%s invalid type "%s", expected a string' % (self.__repr__(), type(sgData).__name__))

    sgData = str(sgData)

    if sgData == self._value:
      return False

    validValues = self.validValues()

    if len(validValues) > 0:
      if not sgData in validValues:
        raise ValueError('%s invalid value "%s"' % (self.__repr__(), sgData))

    self._value = sgData

    return True

    self._value = updateData

    return True

  def _fromFieldData(self, sgData):
    # Dont check for valid values since this function is only given data
    # straight from the Shotgun db.  Fail on Shotguns part if they should ever
    # pass you something that is not a valid value type.

    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    return self._value

class SgFieldSerializable(ShotgunORM.SgField):
  '''
  Entity field that stores serializable data.
  '''

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, dict):
        raise TypeError('%s invalid value type "%s", expected a dict' % (self.__repr__(), type(sgData).__name__))

      sgData = copy.deepcopy(sgData)

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData != None:
      if not isinstance(sgData, dict):
        raise ValueError('%s invalid data from Shotgun "%s", expected a dict' % (self.__repr__(), sgData))

      sgData = copy.deepcopy(sgData)

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _toFieldData(self):
    if self._value == None:
      return None

    return copy.deepcopy(self._value)

  def value(self):
    result = super(SgFieldSerializable, self).value()

    if result == None:
      return None

    return copy.deepcopy(result)

class SgFieldSummary(ShotgunORM.SgField):
  '''
  Entity field that returns an Entity or list of Entities based on a search
  expression.

  Summary fields.
  '''

  DATE_REGEXP = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}) UTC')

  def __init__(self, parentEntity, fieldInfo):
    super(SgFieldSummary, self).__init__(parentEntity, fieldInfo)

    summaryInfo = fieldInfo.summaryInfo()

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
    session = parent.session()

    for c in conditions:
      if c.has_key('logical_operator'):
        logicalOp = {
          'conditions': self._buildLogicalOp(c),
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
              user = session.findOne('HumanUser', [['login', 'is', login]], ['login'])

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

    if self._searchFilter != None:
      return self._searchFilter

    opsRaw = copy.deepcopy(self._filtersRaw)

    logicalOps = {
      'conditions': self._buildLogicalOp(
        opsRaw['conditions'],
        self.parentEntity().session().connection().schema().entityInfo(self.entityType())
      ),
      'logical_operator': opsRaw['logical_operator']
    }

    self._searchFilter = logicalOps

    return self._searchFilter

  def _fetch(self):
    '''
    Internal function do not call!
    '''

    if not self.parentEntity().exists():
      return

    searchExp = self._buildSearchFilter()

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

      self._value = self.parentEntity().session().findOne(self.entityType(), searchExp, order=order)

    ############################################################################
    #
    # Status percentage and list
    #
    ############################################################################
    elif self._summaryType.startswith('status_'):
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if self._summaryType == 'status_percentage':
        if len(sgSearch) <= 0:
          self._value = 0
        else:
          validCount = 0

          for e in sgSearch:
            value = e.field(self._summaryField).value()

            if value == self._summaryValue:
              validCount += 1

          if validCount <= 0:
            self._value = 0.0
          else:
            self._value = float(validCount) / len(sgSearch)
      elif self._summaryType == 'status_list':
        if len(sgSearch) <= 0:
          self._value = 'ip'
        else:
          value = sgSearch[0].field(self._summaryField).value()

          for e in sgSearch[1:]:
            v = e.field(self._summaryField).value()

            if v != value:
              # I have no clue why Shotgun always defaults this result to ip
              # but whatevs yo.
              value = 'ip'

              break

          self._value = value

    ############################################################################
    #
    # Record count
    #
    ############################################################################
    elif self._summaryType == 'record_count':
      # Dont use the orm for this search, waste to build the classes when all
      # we are doing is getting a len on the search result.
      sgSearch = self.parentEntity().session().connection().connection().find(self.entityType(), searchExp)

      self._value = len(sgSearch)
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
      sgSearch = self.parentEntity().session().connection().connection().find(self.entityType(), searchExp, fields=[])

      self._value = len(sgSearch)

    ############################################################################
    #
    # Sum
    #
    ############################################################################
    elif self._summaryType == 'sum':
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        self._value = 0
      else:
        value = 0

        for e in sgSearch:
          v = e.field(self._summaryField).value()

          if v != None:
            value += v

        self._value = value

    ############################################################################
    #
    # Min
    #
    ############################################################################
    elif self._summaryType == 'min':
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        self._value = None
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value = min(v, value)

        self._value = value

    ############################################################################
    #
    # Max
    #
    ############################################################################
    elif self._summaryType == 'max':
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        self._value = None
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value = max(v, value)

        self._value = value

    ############################################################################
    #
    # Average
    #
    ############################################################################
    elif self._summaryType == 'avg':
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        self._value = 0
      else:
        value = sgSearch[0].field(self._summaryField).value()

        for e in sgSearch[1:]:
          v = e.field(self._summaryField).value()

          if v != None:
            value += v

        value = float(value) / len(sgSearch)

        self._value = value

    ############################################################################
    #
    # Percentage
    #
    ############################################################################
    elif self._summaryType == 'percentage':
      sgSearch = self.parentEntity().session().find(self.entityType(), searchExp, fields=[self._summaryField])

      if len(sgSearch) <= 0:
        self._value = 0
      else:
        value = 0

        for e in sgSearch:
          if e.field(self._summaryField).value() == self._summaryValue:
            value += 1

        if value >= 1:
          value = float(value) / len(sgSearch)

        self._value = value

    self._valid = True

  def _fromFieldData(self, sgData):
    '''
    Does nothing.
    '''

    return False

  def _toFieldData(self):
    value = self.value()

    if value == None:
      return None

    result = []

    for i in value:
      result.append(i.toEntityFieldData())

    return result

  def entityType(self):
    '''
    Returns the type of Entity the summary field will return.
    '''

    return self._entityType

  def hasUpdate(self):
    '''
    Always returns False for summary fields.
    '''

    return False

  def setValue(self, value):
    '''
    Does nothing.
    '''

    return False

class SgFieldTagList(ShotgunORM.SgField):
  '''
  Entity field that stores a list of strings.

  The field may contain a list of valid values which when the field is set are
  compared and an Exception thrown when the value is not a valid one.
  '''

  def _setValue(self, sgData):
    if sgData == None or len(sgData) <= 0:
      result = self._value != None and self._value != []

      self._value = []

      return result

    if isinstance(sgData, str):
      sgData = [sgData]
    elif not isinstance(sgData, list):
      raise TypeError('%s invalid type "%s", expected a list' % (self.__repr__(), type(sgData).__name__))

    if len(sgData) <= 0:
      result = self._value != None and self._value != []

      self._value = []

      return result

    newValue = []

    for i in sgData:
      if not isinstance(i, str):
        raise TypeError('%s invalid type "%s" in value "%s", expected a string' % (self.__repr__(), type(i).__name__, sgData))

      newValue.append(i)

    if self._value != None:
      if set(newValue) == set(self._value):
        return False

    validValues = self.validValues()

    if len(validValues) > 0:
      for i in newValue:
        if not i in validValues:
          ValueError('%s invalid value "%s", valid %s' % (self.__repr__(), i, validValues))

    self._value = newValue

    return True

  def _fromFieldData(self, sgData):
    # Dont check for valid values since this function is only given data
    # straight from the Shotgun db.  Fail on Shotguns part if they should ever
    # pass you something that is not a valid value type.

    if sgData == None or len(sgData) <= 0:
      result = self._value != None and self._value != []

      self._value = []

      return result

    if self._value != None:
      if set(newValue) == set(self._value):
        return False

    self._value = list(sgData)

    return True

  def _toFieldData(self):
    return self._value

class SgFieldText(ShotgunORM.SgField):
  '''
  Entity field that stores a str.
  '''

  def _setValue(self, sgData):
    if sgData != None:
      if not isinstance(sgData, (str, unicode)):
        raise TypeError('%s invalid value type "%s", expected a str' % (self.__repr__(), type(sgData).__name__))

      sgData = str(sgData)

    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def _fromFieldData(self, sgData):
    if sgData == self._value:
      return False

    self._value = sgData

    return True

  def toFieldData(self):
    return self._value

class SgFieldImage(SgFieldText):
  '''
  See SgFieldText.
  '''

  def downloadThumbnail(self, path):
    '''
    Downloads the image to the specified path.
    '''

    url = self.value()

    if url == None or url == '':
      raise ValueError('%s value is empty' % self.__repr__())

    if os.path.exists(path) and os.path.isdir(path):
      raise OSError('output path "%s" is a directory' % path)

    try:
      data = urllib2.urlopen(url)

      f = open(path, 'w')

      f.write(data.read())

      f.close()
    except Exception, e:
      ShotgunORM.LoggerEntityField.error(e)

      raise RuntimeError('%s an error occured while downloading the file' % self.__repr__())

    return True

  def openInBrowser(self):
    '''
    Opens the image in a web-browser
    '''

    url = self.value()

    if url == None:
      url = ''

    webbrowser.open(url)

  def uploadThumbnail(self, path):
    '''
    Uploads the specified image file and sets it as the Entities thumbnail.

    Returns the Attachment id.
    '''

    parent = self.parentEntity()

    if not parent.exists():
      raise RuntimeError('parent entity does not exist')

    parent._lock()

    try:
      if self.hasUpdate():
        raise RuntimeError('can not upload a new thumbnail while the image field has an un-commited update')

      sgconnection = parent.session().connection().connection()

      sgResult = sgconnection.upload_thumbnail(parent.type, parent['id'], path)

      parent.sync([self.name()])

      return sgResult
    finally:
      parent._release()

  def uploadFilmstripThumbnail(self, path):
    '''
    Uploads the specified image file and sets it as the Entities flimstrip
    thumbnail.

    Returns the Attachment id.

    Note:
    This function is only valid for Version Entities.
    '''

    parent = self.parentEntity()

    if not parent.type == 'Version':
      raise RuntimeError('only valid on Version Entities')

    if not parent.exists():
      raise RuntimeError('parent entity does not exist')

    parent._lock()

    try:
      if self.hasUpdate():
        raise RuntimeError('can not upload a new thumbnail while the image field has an un-commited update')

      sgconnection = parent.session().connection().connection()

      sgResult = sgconnection.upload_filmstrip_thumbnail(parent.type, parent['id'], path)

      parent.sync([self.name()])

      return sgResult
    finally:
      parent._release()

class SgFieldUrl(ShotgunORM.SgField):
  '''
  Entity field that stores a url.

  Example: {
    'content_type': 'image/jpeg',
    'link_type': 'upload',
    'name': 'bob.jpg',
    'url': 'http://www.owned.com/bob.jpg'
  }
  '''

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

  def _setvalue(self, sgData):
    updateData = self.fromFieldData(sgData)

    if updateData == self._value:
      return False

    self._value = updateData

    return True

  def _fromFieldData(self, sgData):
    result = {}

    if sgData == None:
      return None

    if isinstance(sgData, str):
      sgData = {
        'content_type': None,
        'link_type': 'web',
        'name': os.path.basename(sgData),
        'url': sgData
      }
    elif not isinstance(sgData, dict):
      raise TypeError('%s invalid sgData "%s", expected a dict or string' % (self.__repr__(), sgData))

    try:
      result['url'] = sgData['url']
      result['name'] = sgData.get('name', os.path.basename(result['url']))
      result['content_type'] = sgData.get('content_type', None)

      defaultLinkType = 'web'

      if result['url'].lower().startswith('file:'):
        defaultLinkType = 'local'

      result['link_type'] = sgData.get('link_type', defaultLinkType).lower()
    except:
      raise TypeError('%s invalid sgData dict "%s"' % (self.__repr__(), sgData))

    if not result['link_type'] in ['local', 'upload', 'web']:
      raise ValueError('%s invalid link_type "%s"' % (self.__repr__(), result['link_type']))

    #if result['link_type'] == 'upload':
    #  ctype = result['content_type']
    #
    #  if ctype == None:
    #    raise ValueError('%s content_type can not be None when link_type is upload' % self.__repr__())
    #
    #  if not ctype.startswith('image/'):
    #    raise ValueError('%s invalid content_type "%s"' % (self.__repr__(), ctype))

    return result

  def _toFieldData(self):
    if self._value == None:
      return None

    return copy.deepcopy(self._value)

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
ShotgunORM.SgField.registerFieldClass(ShotgunORM.SgField.RETURN_TYPE_URL, SgFieldUrl)
