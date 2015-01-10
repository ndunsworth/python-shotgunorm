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
  'SgApiInfo'
]

# Python imports
import weakref

class SgApiInfo(object):
  '''
  Class that represents the API information of a Shotgun connection.
  '''

  def __repr__(self):
    return '<SgApiInfo: %d.%dv%d>' % tuple(self.version())

  def __str__(self):
    return 'Shotgun %d.%dv%d' % tuple(self.version())

  def __init__(self, sgConnection):
    self.__connection = weakref.ref(sgConnection)

    self.__majVersion = None
    self.__minVersion = None
    self.__relVersion = None
    self.__totangoId = None
    self.__totangoName = None
    self.__s3Enabled = False

    self.refresh()

  def connection(self):
    '''
    Returns the Shotgun connection the info belongs to.
    '''

    return self.__connection()

  def hasS3(self):
    '''
    Returns True if the Shotgun instance has Amazon s3 uploads enabled.
    '''

    return self.__s3Enabled

  def isValid(self):
    '''
    Returns True if the info is valid.
    '''

    return self.__majVersion != None

  def majorVersion(self):
    '''
    Returns the major version number of the Shotgun instance.
    '''

    return self.__majVersion

  def minorVersion(self):
    '''
    Returns the minor version number of the Shotgun instance.
    '''

    return self.__minVersion

  def refresh(self):
    '''
    Refreshes the api info from Shotgun.
    '''

    connection = self.connection()

    if connection == None:
      return False

    try:
      info = connection.connection().info()
    except:
      return False

    self.__majVersion, self.__minVersion, self.__relVersion = info['version']
    self.__totangoId = info['totango_site_id']
    self.__totangoName = info['totango_site_name']
    self.__s3Enabled = info['s3_uploads_enabled']

    return True

  def releaseVersion(self):
    '''
    Returns the release version number of the Shotgun instance.
    '''

    return self.__relVersion

  def totangoId(self):
    '''
    Returns the Totango site id.
    '''

    return self.__totangoId

  def totangoName(self):
    '''
    Returns the Totango site name.
    '''

    return self.__totangoName

  def version(self):
    '''
    Returns a list of the major, minor, relase information of the Shotgun
    instance.
    '''

    return [
      self.__majVersion,
      self.__minVersion,
      self.__relVersion
    ]
