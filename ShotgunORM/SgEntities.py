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

class SgApiUser(SgEntity):
  '''
  Class that represents a Api User Entity.
  '''

  pass

class SgAppWelcome(SgEntity):
  '''
  Class that represents a AppWelcome Entity.
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

  def sendEmail(self, subject, msg, cc=[], sender='mr.roboto@leetstudios.com', server='localhost'):
    '''
    Send the user an email.

    The arg "cc" should be a list of other SgHumanUser objects.
    '''

    email = self['email']

    if email == '' or email.isspace():
      raise RuntimeError('email field is emtpy')

    ccEmails = []

    for i in cc:
      if not isinstance(i, SgHumanUser):
        raise TypeError('expected a SgHumanUser, got "%s"' % i.__class__.__name__)

      ccEmail = i['email']

      if ccEmail == '' or ccEmail.isspace():
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

  def sendInstantMessage(self, subject, msg):
    '''
    Sens the user an instant message.
    '''

    raise RuntimeError('not implemented')

  def tasks(self, extraSgFilters='', extraSgFilterArgs=[]):
    '''
    Returns all the Tasks the user belongs to.

    Args:
      * extraSgFilters:
        Addtional search expression to append when finding Tasks.

      * extrSgFilterArgs:
        List of args passed to the session.search() function.
    '''

    searchExp = 'task_assignees in [%s]' % self.toEntityFieldData()

    if extraSgFilters != None:
      if len(extraSgFilters) >= 1 and not extraSgFilters.isspace():
        searchExp += ' and ' + extraSgFilters

    return self.session().search('Task', searchExp, sgSearchArgs=extraSgFilterArgs)

class SgNote(SgEntity):
  '''
  Class that represents a Note Entity.
  '''

  pass

class SgTicket(SgEntity):
  '''
  Class that represents a Ticket Entity.
  '''

  def reply(self, sgMsg, sgUser=None, sgCommit=True):
    '''
    Creates a reply to the ticket.

    When the arg "sgUser", valid value types (SgApiUser, SgHumanUser or str), is
    specified the ticket will be a reply from that user.

    Returns the Reply Entity.

    Note:
    If the arg "sgCommit" is False then the returned Reply Entity has not yet
    been published to Shotgun.  You must call commit() on the returned Entity.
    '''

    session = self.session()

    replyData = None

    if sgUser != None:
      if isinstance(sgUser, str):
        user = session.findOne('HumanUser', [['name', 'is', sgUser]])

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

    result = session.create('Reply', replyData, sgCommit=sgCommit)

    return result

class SgVersion(SgEntity):
  '''
  Class that represents a Version Entity.
  '''

  REGEXP_VER = re.compile(r'([_.]v)(\d+)(s(\d+))?$')

  def _changeVersion(self, value, doSub=False, valueIsVersion=False, ignoreProject=False):
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

    project = self.toFieldData(['project'])['project']

    searchFilters = [
      ['code', 'is', newVersion],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.toFieldData(['project'])['project']
        ]
      )

    return self.session().findOne('Version', searchFilters, ['code', 'project'])

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

  def prevSubVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous sub-version of this one.

    When no previous sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    return self._changeVersion(-1, True, ignoreProject=ignoreProject)

  def prevVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the previous version of this one.

    When no previous version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    return self._changeVersion(-1, False, ignoreProject=ignoreProject)

  def nextSubVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the next sub-version of this one.

    When no higher sub-version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    return self._changeVersion(1, True, ignoreProject=ignoreProject)

  def nextVersion(self, ignoreProject=False):
    '''
    Returns the Version Entity that is the next version of this one.

    When no higher version exists returns None.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    return self._changeVersion(1, False)

  def otherSubVersions(self, ignoreProject=False):
    '''
    Returns all sub-versions but not including this one.
    '''

    name = self['code']

    search = self.REGEXP_VER.search(name)

    if search == None or search.groups()[3] == None:
      return []

    searchFilters = [
      ['code', 'starts_with', name[:search.spans()[3][0]]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.toFieldData(['project'])['project']
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    return self.session().find('Version', searchFilters, ['code', 'project'])

  def otherVersions(self, ignoreProject=False):
    '''
    Returns all versions but not including this one.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    name = self['code']

    search = self.REGEXP_VER.search(name)

    if search == None:
      return []

    project = self.toFieldData(['project'])['project']

    searchFilters = [
      ['code', 'starts_with', name[:search.span()[0] + 2]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.toFieldData(['project'])['project']
        ]
      )

    if self.exists():
      searchFilters.append(['id', 'is_not', self['id']])

    return self.session().find('Version', searchFilters, ['code', 'project'])

  def subVersion(self, subVersion, ignoreProject=False):
    '''
    Returns the Version Entity that is the sub-version specified by arg
    "subVersion".  The returned result can be the same Entity.

    When the specified sub-version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.
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

  def subVersions(self, ignoreProject=False):
    '''
    Returns all sub-versions.
    '''

    name = self['code']

    search = self.REGEXP_VER.search(name)

    if search == None or search.groups()[3] == None:
      return []

    project = self.toFieldData(['project'])['project']

    searchFilters = [
      ['code', 'starts_with', name[:search.spans()[3][0]]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.toFieldData(['project'])['project']
        ]
      )

    return self.session().find('Version', searchFilters, ['code', 'project'])

  def version(self, version, ignoreProject=False):
    '''
    Returns the Version Entity that is the version specified by arg "version".
    The returned result can be the same Entity.

    When the specified version does not exist returns None.

    Note:
    This is performs a Shotgun search for its return value.
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

  def versions(self, ignoreProject=False):
    '''
    Returns all versions.

    Note:
    This is performs a Shotgun search for its return value.
    '''

    name = self['code']

    search = self.REGEXP_VER.search(name)

    if search == None:
      return []

    project = self.toFieldData(['project'])['project']

    searchFilters = [
      ['code', 'starts_with', name[:search.span()[0] + 2]],
    ]

    if not ignoreProject:
      searchFilters.append(
        [
          'project',
          'is',
          self.toFieldData(['project'])['project']
        ]
      )

    return self.session().find('Version', searchFilters, ['code', 'project'])
