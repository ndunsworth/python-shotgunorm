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
  'SgVersion'
]

# Python imports
import re

# This module imports
import ShotgunORM

class SgVersion(ShotgunORM.SgEntity):
  '''
  Class that represents a Version Entity.
  '''

  REGEXP_VER = re.compile(r'([_.]v)(\d+)(s(\d+))?$')

  def _changeVersion(
    self,
    value,
    sgFields=None,
    doSub=False, valueIsVersion=False,
    ignoreProject=False
  ):
    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    if name == None or name == '':
      return None

    search = self.REGEXP_VER.search(name)

    if search == None:
      return None

    spans = search.groups()

    pre = spans[0]
    ver = spans[1]
    post = spans[2]
    subv = spans[3]

    if doSub and subv == None:
      return None

    result = None

    newVersion = None

    if doSub:
      if valueIsVersion:
        if value == int(subv):
          return self

        newVersion = ''.join(
          [
            name[:search.span()[0]],
            pre,
            ver,
            post,
            str(max(1, value)).zfill(len(subv))
          ]
        )
      else:
        padding = len(subv)

        newVer = max(1, int(subv) + value)

        if newVer == int(subv):
          return None

        newsubv = str(newVer).zfill(padding)

        newVersion = ''.join(
          [
            name[:search.span()[0]],
            pre,
            ver,
            post,
            subv
          ]
        )
    else:
      if valueIsVersion:
        if value == int(ver):
          return self

        padding = len(ver)

        ver = str(max(1, value)).zfill(padding)

        tmp = ''.join([pre, ver])

        if post != None:
          tmp = ''.join([tmp, post, subv])

        newVersion = ''.join(
          [
            name[:search.span()[0]],
            tmp
          ]
        )
      else:
        padding = len(ver)

        newVer = max(1, int(ver) + value)

        if newVer == int(ver):
          return None

        ver = str(newVer).zfill(padding)

        tmp = ''.join([pre, ver])

        if post != None:
          tmp = ''.join([tmp, post, subv])

        newVersion = ''.join(
          [
            name[:search.span()[0]],
            tmp
          ]
        )

    searchFilters = [
      ['code', 'is', newVersion],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.update(['default', 'code', 'project'])

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.update(['code', 'project'])

      sgFields = list(sgFields)

    return self.connection().findOne('Version', searchFilters, sgFields)

  def isSubVersioned(self):
    '''
    Returns True if the code field contains a sub-version number.
    '''

    search = self.REGEXP_VER.search(self['code'])

    if search == None:
      return False

    return search.groups()[3] != None

  def isVersioned(self):
    '''
    Returns True if the code field contains a version number.
    '''

    search = self.REGEXP_VER.search(self['code'])

    return search != None

  def latestSubVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the highest sub-version in Shotgun.

    If no higher sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned() or not self.isSubVersioned():
      return None

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    startIndex = search.span()[0]

    for n in search.groups()[0:2]:
      startIndex += len(n)

    searchFilters = [
      ['code', 'starts_with', name[:startIndex]]
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    otherVersions = self.connection().find('Version', searchFilters, sgFields)

    if len(otherVersions) <= 0:
      return None

    highestVer = None
    highestVerInt = -1

    for version in otherVersions:
      v = version.versionNumber()

      if v > highestVerInt:
        highestVer = version
        highestVerInt = v

    return highestVer

  def latestVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the highest version in Shotgun.

    If no higher version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned():
      return None

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    searchFilters = [
      ['code', 'starts_with', name[:search.span()[0] + 2]]
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    otherVersions = self.connection().find('Version', searchFilters, sgFields)

    if len(otherVersions) <= 0:
      return None

    highestVer = None
    highestVerInt = -1

    for version in otherVersions:
      v = version.versionNumber()

      if v > highestVerInt:
        highestVer = version
        highestVerInt = v

    return highestVer

  def prevSubVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous sub-version of this one.

    When no previous sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(-1, doSub=True, sgFields=sgFields, ignoreProject=ignoreProject)

  def prevVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous version of this one.

    When no previous version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(-1, doSub=False, sgFields=sgFields, ignoreProject=ignoreProject)

  def nextSubVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the next sub-version of this one.

    When no higher sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(1, doSub=True, sgFields=sgFields, ignoreProject=ignoreProject)

  def nextVersion(self, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the next version of this one.

    When no higher version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(1, doSub=False, sgFields=sgFields, ignoreProject=ignoreProject)

  def otherSubVersions(self, sgFields=None, ignoreProject=False):
    '''
    Returns all sub-versions but not including this one.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned() or not self.isSubVersioned():
      return []

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    startIndex = search.span()[0]

    for n in search.groups()[0:2]:
      startIndex += len(n)

    searchFilters = [
      ['code', 'starts_with', name[:startIndex]]
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    return self.connection().find('Version', searchFilters, sgFields)

  def otherVersions(self, sgFields=None, ignoreProject=False):
    '''
    Returns all versions but not including this one.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned():
      return []

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    searchFilters = [
      ['code', 'starts_with', name[:search.span()[0] + 2]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    return self.connection().find('Version', searchFilters, sgFields)

  def subVersion(self, subVersion, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the sub-version specified by arg
    "subVersion".  The returned result can be the same Entity.

    When the specified sub-version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    if int(subVersion) == self.subVersionNumber():
      return self

    return self._changeVersion(int(subVersion), doSub=True, valueIsVersion=True, sgFields=sgFields, ignoreProject=ignoreProject)

  def subVersionNumber(self):
    '''
    Returns the version number.

    If the code field contains no version returns None.
    '''

    search = self.REGEXP_VER.search(self['code'])

    if search == None or search.group(4) == None:
      return None

    return int(search.group(4))

  def subVersionNumberPadding(self):
    '''
    Returns the number padding for the sub-version.
    '''

    search = self.REGEXP_VER.search(self['code'])

    if search == None or search.group(4) == None:
      return None

    return len(search.group(4))

  def subVersions(self, sgFields=None, ignoreProject=False):
    '''
    Returns all sub-versions.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned() or not self.isSubVersioned():
      return []

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    return self.connection().find('Version', searchFilters)

  def version(self, version, sgFields=None, ignoreProject=False):
    '''
    Returns the Version Entity that is the version specified by arg "version".
    The returned result can be the same Entity.

    When the specified version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the result with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    if int(version) == self.versionNumber():
      return self

    return self._changeVersion(int(version), doSub=False, valueIsVersion=True, sgFields=sgFields, ignoreProject=ignoreProject)

  def versionNumber(self):
    '''
    Returns the version number.

    If the code field contains no version returns None.
    '''

    search = self.REGEXP_VER.search(self['code'])

    if search == None:
      return None

    return int(search.group(2))

  def versionNumberPadding(self):
    '''
    Returns the number padding of the version.
    '''

    search = self.REGEXP_VER.search(self['code'])

    if search == None:
      return None

    return len(search.group(2))

  def versions(self, sgFields=None, ignoreProject=False):
    '''
    Returns all versions.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    # Bail if not versioned!
    if not self.isVersioned():
      return []

    self.sync(
      ['code', 'project'],
      ignoreValid=True,
      ignoreWithUpdate=True,
      backgroundPull=True
    )

    name = self['code']

    search = self.REGEXP_VER.search(name)

    searchFilters = [
      ['code', 'starts_with', name[:search.span()[0] + 2]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.field('project').toFieldData()
        ]
      )

    if sgFields == None:
      sgFields = self.connection().defaultEntityQueryFields('Version')

      sgFields.add('code')

      sgFields = list(sgFields)
    else:
      sgFields = set(sgFields)

      sgFields.add('code')

      sgFields = list(sgFields)

    return self.connection().find('Version', searchFilters, sgFields)

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgVersion,
  sgEntityTypes=['Version']
)
