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
  'SgUserFieldAbstractEntity',
  'SgUserFieldAbstractMultiEntity'
]

# This module imports
import ShotgunORM

class SgUserFieldAbstractEntity(ShotgunORM.SgUserField):
  '''
  A base class which can be used for user fields that return an Entity as their
  value.
  '''

  def _fromFieldData(self, sgData):
    if sgData == None:
      result = self._value != None

      self._value = None

      return result

    try:
      newValue = {
        'type': sgData['type'],
        'id': sgData['id']
      }

      if sgData.has_key('name'):
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

    return dict(self._value)

  def value(self, sgSyncFields=None):
    '''
    Returns the fields value as a Entity object.

    Args:
      * (list) sgSyncFields:
        List of field names to populate the returned Entity with.
    '''

    v = super(SgUserFieldAbstractEntity, self).value()

    parent = self.parentEntity()

    if v == None or parent == None:
      return None

    connection = parent.connection()

    if sgSyncFields == None:
      sgSyncFields = connection.defaultEntityQueryFields(v['type'])

      if len(sgSyncFields) <= 0:
        sgSyncFields = None
    else:
      pullFields = []

      if isinstance(sgSyncFields, str):
        pullFields = set([sgSyncFields])
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

        extraFields = connection.defaultEntityQueryFields(v['type'])

      pullFields.update(extraFields)

      if len(pullFields) >= 1:
        sgSyncFields = list(pullFields)
      else:
        sgSyncFields = None

    result = connection._createEntity(
      v['type'],
      v,
      sgSyncFields=sgSyncFields
    )

    return result

class SgUserFieldAbstractMultiEntity(ShotgunORM.SgUserField):
  '''
  A base class which can be used for user fields that return a list of Entity
  objects as their value.
  '''

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

        if i.has_key('name'):
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

    result = []

    for i in self._value:
      result.append(dict(i))

    return result

  def value(self, sgSyncFields=None):
    '''
    Returns the fields value as a list of Entity objects.

    Args:
      * (list) sgSyncFields:
        List of field names to populate the returned Entities with.
    '''

    result = super(SgUserFieldAbstractMultiEntity, self).value()

    if result in [None, []]:
      return result

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
