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
  'SgHumanUser'
]

# Python imports
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import smtplib

# This module imports
import ShotgunORM

class SgHumanUser(ShotgunORM.SgEntity):
  '''
  Class that represents a Human User Entity.
  '''

  def notes(self, sgFields=None, order=None, limit=0, retired_only=False, page=0):
    '''
    Returns all the Notes created by the user.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (list) order:
        List of Shotgun formatted order filters.

      * (int) limit:
        Limits the amount of Entities can be returned.

      * (bool) retired_only:
        Return only retired entities.

      * (int) page:
        Return a single specified page number of records instead of the entire
        result set.
    '''

    if not self.exists():
      return []

    result = self.connection().find(
      'Note',
      [['user', 'is', self]],
      sgFields,
      order=order,
      limit=limit,
      retired_only=retired_only,
      page=page
    )

    if limit == 1:
      if len(result) <= 0:
        return None
      else:
        return result[0]
    else:
      return result

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

  def tasks(self, sgFields=None, order=None, limit=0, retired_only=False, page=0):
    '''
    Returns all the Tasks the user belongs to.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (list) order:
        List of Shotgun formatted order filters.

      * (int) limit:
        Limits the amount of Entities can be returned.

      * (bool) retired_only:
        Return only retired entities.

      * (int) page:
        Return a single specified page number of records instead of the entire
        result set.
    '''

    if not self.exists():
      return []

    result = self.connection().find(
      'Task',
      [['task_assignees', 'is', self]],
      sgFields,
      order=order,
      limit=limit,
      retired_only=retired_only,
      page=page
    )

    if limit == 1:
      if len(result) <= 0:
        return None
      else:
        return result[0]
    else:
      return result

  def tickets(self, sgFields=None, order=None, limit=0, retired_only=False, page=0):
    '''
    Returns all the Tickets assigned to the user.

    Args:
      * (list) sgFields:
        List of fields to populate the results with.

      * (list) order:
        List of Shotgun formatted order filters.

      * (int) limit:
        Limits the amount of Entities can be returned.

      * (bool) retired_only:
        Return only retired entities.

      * (int) page:
        Return a single specified page number of records instead of the entire
        result set.
    '''

    if not self.exists():
      return []

    result = self.connection().find(
      'Ticket',
      [['addressings_to', 'is', self]],
      sgFields,
      order=order,
      limit=limit,
      retired_only=retired_only,
      page=page
    )

    if limit == 1:
      if len(result) <= 0:
        return None
      else:
        return result[0]
    else:
      return result

# Register the custom class.
ShotgunORM.SgEntity.registerDefaultEntityClass(
  sgEntityCls=SgHumanUser,
  sgEntityTypes=['HumanUser']
)
