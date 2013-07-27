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
  'SgApiUser',
  'SgAppWelcome',
  'SgAsset',
  'SgBanner',
  'SgHumanUser',
  'SgNote',
  'SgPhase',
  'SgProject',
  'SgTask',
  'SgTicket',
  'SgVersion'
]

# Python imports
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import re
import smtplib

# This module imports
from SgEntity import SgEntity
from SgField import SgField

class SgApiUser(SgEntity):
  '''
  Class that represents a Api User Entity.
  '''

  pass

class SgAppWelcome(SgEntity):
  '''
  Class that represents a AppWelcome Entity.

  This Entity does nothing and is used by HumanUser Entities.

  This class is just a place holder.
  '''

  pass

class SgBanner(SgEntity):
  '''
  Class that represents a Banner Entity.

  This Entity does nothing and is used by HumanUser Entities.

  This class is just a place holder.
  '''

  pass

class SgAsset(SgEntity):
  '''
  Class that represents a Asset Entity.
  '''

  pass

class SgHumanUser(SgEntity):
  '''
  Class that represents a Human User Entity.
  '''

  def sendEmail(self, subject, msg, cc=None, sender='mr.roboto@leetstudios.com', server='localhost'):
    '''
    Send the user an email.

    The arg "cc" should be a list of other SgHumanUser objects or strings.

    Args:
      * (str) subject:
        Email subject string.

      * (str) msg:
        Email message.

      * (list) cc:
        List of HumanUser or strings that will be cc'd.

      * (str) sender:
        Return email address.

      * (str) server:
        Email server ip.
    '''

    email = self['email']

    if email == '' or email.isspace():
      raise RuntimeError('email field is emtpy')

    ccEmails = []

    if cc != None:
      for i in cc:
        if not isinstance(i, SgHumanUser):
          raise TypeError('expected a SgHumanUser, got "%s"' % i.__class__.__name__)

        ccEmail = i['email']

        if ccEmail == None or ccEmail == '' or ccEmail.isspace():
          raise RuntimeError('HumanUser %s\'s email field is emtpy' % i['name'])

        ccEmails.append(ccEmail)

    emailInfo = MIMEMultipart()

    emailInfo['From'] = sender
    emailInfo['To'] = email

    if len(ccEmails) >= 1:
      emailInfo['CC'] = ','.join(ccEmails)

    emailInfo['Subject'] = subject

    emailMsg = MIMEText(msg)
    emailMsg.add_header('Content-Disposition', 'inline')

    emailInfo.attach(emailMsg)

    serverSmtp = smtplib.SMTP(server, 25)
    #serverSmtp.debuglevel = 5

    serverSmtp.sendmail(emailInfo['From'], [emailInfo['TO']] + ccEmails, emailInfo.as_string())

  def sendInstantMessage(self, msg):
    '''
    Sends the user an instant message.

    Default function raises a RuntimeError of "not implemented".

    Args:
      * (str) msg:
        Message string.
    '''

    raise RuntimeError('not implemented')

  def tasks(self, extraSgFilters=None, extraSgFilterArgs=None):
    '''
    Returns all the Tasks the user belongs to.

    Args:
      * (list) extraSgFilters:
        Addtional search expression to append when finding Tasks.

      * (list) extrSgFilterArgs:
        List of args passed to the connection.search() function.
    '''

    searchExp = 'task_assignees in [%s]' % self.toEntityFieldData()

    if extraSgFilters != None:
      if len(extraSgFilters) >= 1 and not extraSgFilters.isspace():
        searchExp += ' and ' + extraSgFilters

    return self.connection().search('Task', searchExp, sgSearchArgs=extraSgFilterArgs)

class SgNote(SgEntity):
  '''
  Class that represents a Note Entity.
  '''

  pass

# Fix for the lame ass return type "color2".  See ShotgunORM.SgFieldColor2 for more
# information on this lovely mess.
class SgPhase(SgEntity):
  '''
  Class that represents a Phase Entity.
  '''

  def _buildFields(self, sgFieldInfos):
    '''
    Subclass portion of SgEntity.buildFields().

    Note:
    Do not call this directly!
    '''

    colorFieldInfo = sgFieldInfos['color']

    del sgFieldInfos['color']

    fieldClasses = SgField.__fieldclasses__

    self._fields['color'] = fieldClasses.get(SgField.RETURN_TYPE_COLOR2, None)(self, colorFieldInfo)

    super(SgPhase, self)._buildFields(sgFieldInfos)

class SgProject(SgEntity):
  '''
  Class that represents a Project Entity.
  '''

  def sequenceNames(self):
    '''
    Returns a list of all Sequence names for this project.
    '''

    result = []

    if not self.exists():
      return result

    seqs = self.sequences(sgFields=['code'])

    for seq in seqs:
      result.append(seq['code'])

    result.sort()

    return result

  def sequences(self, sgFields=None):
    '''
    Returns a list of all Sequence Entities for this project.

      * (list) sgFields:
        List of fields to populate the results with.
    '''

    if not self.exists():
      return []

    return self.connection().find(
      'Sequence',
      [
        [
          'project',
          'is',
          self
        ]
      ],
      sgFields
    )

  def shotNames(self, sgSequences=None):
    '''
    Returns a dict containing of all Shot names for this project.

    Args:
      * (list) sgSequences:
        Return only the Shot names associated with the list of Sequences.
    '''

    result = {}

    if not self.exists():
      return result

    seqShots = self.shots(sgFields=['code'])

    for seq, shots in seqShots.items():
      shotNames = []

      for shot in shots:
        shotNames.append(shot['code'])

      result[seq] = shotNames

    return result

  def shots(self, sgSequences=None, sgFields=None):
    '''
    Returns a dict of all Shot Entities for this project.

    Args:
      * (list) sgSequences:
        Return only the Shots associated with the list of Sequences.

      * (list) sgFields:
        List of fields to populate the results with.
    '''

    if not self.exists():
      return {}

    if isinstance(sgSequences, (str, SgEntity)):
      sgSequences = [sgSequences]

    if sgSequences == None:
      sgSequences = self.sequenceNames()

    result = {}

    if len(sgSequences) <= 0:
      return result

    seqNames = []

    for seq in sgSequences:
      if isinstance(seq, str):
        seqNames.append(seq)
      else:
        seqNames.append(seq['code'])

    qEngine = self.connection().queryEngine()

    # Block the query engine so all Shot fields get pulled at once.
    qEngine.block()

    try:
      sequences = self.connection().find(
        'Sequence',
        [
          [
            'project',
            'is',
            self
          ],
          [
            'code',
            'in',
            seqNames
          ]
        ],
        ['shots']
      )

      for seq in sequences:
        seqField = seq.field('shots')

        result[seq['code']] = seqField.value(sgSyncFields={'Shot': sgFields})
    finally:
      qEngine.unblock()

    return result

# Fix for the lame ass return type "color2".  See ShotgunORM.SgFieldColor2 for more
# information on this lovely mess.
class SgTask(SgEntity):
  '''
  Class that represents a Task Entity.
  '''

  def _buildFields(self, sgFieldInfos):
    '''
    Subclass portion of SgEntity.buildFields().

    Note:
    Do not call this directly!
    '''

    colorFieldInfo = sgFieldInfos['color']

    del sgFieldInfos['color']

    fieldClasses = SgField.__fieldclasses__

    self._fields['color'] = fieldClasses.get(SgField.RETURN_TYPE_COLOR2, None)(self, colorFieldInfo)

    super(SgTask, self)._buildFields(sgFieldInfos)


class SgTicket(SgEntity):
  '''
  Class that represents a Ticket Entity.
  '''

  def reply(self, sgMsg, sgUser=None, sgCommit=False):
    '''
    Creates a reply to the ticket.

    When the arg "sgUser", valid value types (SgApiUser, SgHumanUser or str), is
    specified the ticket will be a reply from that user.

    Returns the Reply Entity.

    Note:
    If the arg "sgCommit" is False then the returned Reply Entity has not yet
    been published to Shotgun.  You must call commit() on the returned Entity.

    Args:
      * (str) sgMsg:
        Reply message.

      * (HumanUser, str) sgUser:
        User which the replay will originate from.  If left as None then the
        connections SgApiUser will be used.

      * (bool) sgCommit:
        Commit the reply immediately.
    '''

    connection = self.connection()

    replyData = None

    if sgUser != None:
      if isinstance(sgUser, str):
        user = connection.findOne('HumanUser', [['name', 'is', sgUser]])

        if user == None:
          raise RuntimeError('unable to find HumanUser "%s"' % sgUser)

        sgUser = user
      elif not isinstance(sgUser, (SgApiUser, SgHumanUser)):
        raise TypeError('expected a ApiUser/HumanUser Entity or a user name, got %s' % sgUser.__class__.__name__)

      replyData = {
        'content': sgMsg,
        'entity': self.toEntityFieldData(),
        'user': sgUser.toEntityFieldData()
      }
    else:
      replyData = {
        'content': sgMsg,
        'entity': self.toEntityFieldData(),
      }

    result = connection.create('Reply', replyData, sgCommit=sgCommit)

    return result

  def close(self, sgMsg, sgUser=None, sgCommit=False):
    '''
    Sets the tickets status to closed and creates a reply.

    Returns the reply Entity.

    Args:
      * (str) sgMsg:
        Reply message.

      * (HumanUser, str) sgUser:
        User which the replay will originate from.  If left as None then the
        connections SgApiUser will be used.

      * (bool) sgCommit:
        Commit the reply immediately.
    '''

    with self:
      if not isinstance(sgMsg, str):
        raise TypeError('expected a str for "sgMsg" got %s' % sgMsg)

      if sgUser != None:
        if isinstance(sgUser, str):
          user = sg.searchOne('HumanUser', 'name == "%s"' % sgUser)

          if user == None:
            raise RuntimeError('not able to find Shotgun user "%s"' % sgUser)

          sgUser = user
        elif isinstance(sgUser, SgEntity):
          if not sgUser.type == 'HumanUser':
            raise TypeError('invalid entity type "%s" expected a HumanUser' % sgUser.type)

      fieldStatus = self.field('sg_status_list')

      fieldStatus.setValue('res')

      connection = self.connection()

      replyEntity = connection.create('Reply', {
        'content': sgMsg,
        'entity': self.toEntityFieldData()
      })

      if sgUser != None:
        replyEntity['user'] = sgUser

      if not sgCommit:
        return replyEntity

      batchData = []

      if fieldStatus.hasCommit():
        batchData.append(
          {
            'entity': self,
            'batch_data': self.toBatchData(['sg_status_list'])
          }
        )

      batchData.append(
        {
          'entity': replyEntity,
          'batch_data': replyEntity.toBatchData()
        }
      )

      connection._batch(batchData)

      return replyEntity

class SgVersion(SgEntity):
  '''
  Class that represents a Version Entity.
  '''

  REGEXP_VER = re.compile(r'([_.]v)(\d+)(s(\d+))?$')

  def _changeVersion(self, value, doSub=False, valueIsVersion=False, ignoreProject=False):
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

    return self.connection().findOne('Version', searchFilters, ['default', 'code', 'project'])

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

  def latestSubVersion(self, ignoreProject=False):
    '''
    Returns the highest sub-version in Shotgun.

    If no higher sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    otherVersions = self.connection().find('Version', searchFilters, ['code'])

    if len(otherVersions) <= 0:
      return None

    highestVer = None
    highestVerInt = -1

    for version in otherVersions:
      v = version.versionNumber()

      if v > highestVerInt:
        highestVer = version
        highestVerInt = v

    if highestVer != None:
      fields = self.connection().defaultEntityQueryFields('Version')

      if len(fields) >= 1:
        highestVer.sync(
          fields,
          ignoreValid=True,
          ignoreWithUpdate=True,
          backgroundPull=True
        )

    return highestVer

  def latestVersion(self, ignoreProject=False):
    '''
    Returns the highest version in Shotgun.

    If no higher version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    otherVersions = self.connection().find('Version', searchFilters, ['code'])

    if len(otherVersions) <= 0:
      return None

    highestVer = None
    highestVerInt = -1

    for version in otherVersions:
      v = version.versionNumber()

      if v > highestVerInt:
        highestVer = version
        highestVerInt = v

    if highestVer != None:
      fields = self.connection().defaultEntityQueryFields('Version')

      if len(fields) >= 1:
        highestVer.sync(
          fields,
          ignoreValid=True,
          ignoreWithUpdate=True,
          backgroundPull=True
        )

    return highestVer

  def prevSubVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous sub-version of this one.

    When no previous sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(-1, True, ignoreProject=ignoreProject)

  def prevVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous version of this one.

    When no previous version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(-1, False, ignoreProject=ignoreProject)

  def nextSubVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the next sub-version of this one.

    When no higher sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(1, True, ignoreProject=ignoreProject)

  def nextVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the next version of this one.

    When no higher version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(1, False)

  def otherSubVersions(self, ignoreProject=False):
    '''
    Returns all sub-versions but not including this one.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    return self.connection().find('Version', searchFilters)

  def otherVersions(self, ignoreProject=False):
    '''
    Returns all versions but not including this one.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    return self.connection().find('Version', searchFilters)

  def subVersion(self, subVersion, ignoreProject=False):
    '''
    Returns the Version Entity that is the sub-version specified by arg
    "subVersion".  The returned result can be the same Entity.

    When the specified sub-version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(int(subVersion), True, True, ignoreProject=ignoreProject)

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

  def subVersions(self, ignoreProject=False):
    '''
    Returns all sub-versions.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    return self.connection().find('Version', searchFilters)

  def version(self, version, ignoreProject=False):
    '''
    Returns the Version Entity that is the version specified by arg "version".
    The returned result can be the same Entity.

    When the specified version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
      * (bool) ignoreProject:
        Ignore the project field when searchign for other versions.
    '''

    return self._changeVersion(int(version), False, True, ignoreProject=ignoreProject)

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

  def versions(self, ignoreProject=False):
    '''
    Returns all versions.

    Note:
    This is performs a Shotgun search for its return value.

    Args:
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

    return self.connection().find('Version', searchFilters)
