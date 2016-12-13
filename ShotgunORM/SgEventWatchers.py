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
  'SgEntryTypeFilter',
  'SgEntryTypeEventHandler',
  'SgFileEventHandler',
  'SgProjectFilter',
  'SgStreamEventHandler',
  'SgUDPBroadcastEventHandler',
]

# Python imports
import os
import socket
import sys

# This module imports
import ShotgunORM

########################################################################
#
# Filters
#
########################################################################

class SgEntryTypeFilter(ShotgunORM.SgEventFilter):
  '''
  Event filter class that bases its filter by event types.
  '''

  def __init__(self, sgEventTypes):
    super(SgTypeFilter, self).__init__()

    self.__eventTypes = list(sgEventTypes)

  def eventTypes(self):
    '''
    Returns a list of valid event_type values the filter will return True for.
    '''

    return list(self.__eventTypes)

  def filter(self, sgEvent):
    '''
    Returns True if the sgEvent.type() matches on of the filters eventTypes().

    Args:
      * (SgEvent) sgEvent:
        Event to filter.
    '''

    return sgEvent.type() in self.__eventTypes

class SgProjectFilter(ShotgunORM.SgEventFilter):
  '''
  Event filter class that filters events for a specific project.
  '''

  def __init__(self, project):
    self._project = project

  def filter(self, sgEvent):
    '''
    Returns True if the events project matches the filters project.
    '''

    return self._project == sgEvent.project

  def project(self):
    '''

    '''

    return self._project

########################################################################
#
# Handlers
#
########################################################################

class SgEntryTypeEventHandler(ShotgunORM.SgEventHandler):
  '''
  Event handler class that bases its filtering by event types.
  '''

  def __init__(self, sgEventTypes):
    super(SgTypeEventHandler, self).__init__()

    self.addFilter(SgTypeFilter(sgEventTypes))

class SgStreamEventHandler(ShotgunORM.SgEventHandler):
  '''
  Event handler class that sends events to an ostream.
  '''

  def __init__(self, stream=None):
    super(SgStreamEventHandler, self).__init__()

    if stream == None:
      stream = sys.stdout

    self._stream = stream

  def flush(self):
    '''
    Flush the handlers stream.

    This function looks for an attribute on the stream called "flush" and if it
    exists calls it.
    '''

    with self:
      if hasattr(self._stream, 'flush'):
        self._stream.flush()

  def formatMessage(self, sgEvent):
    '''
    Returns a formatted string for the event.

    Subclasses can override this function to return custom msgs.

    Args:
      * (SgEvent) sgEvent:
        Event to build message for.
    '''

    return (
      ShotgunORM.formatSerializable(
        sgEvent.event().fieldValues()
      ) + '\n'
    )

  def processEvent(self, sgEvent):
    '''
    Processes the event and writes a formatted string to the handlers stream.

    Args:
      * (SgEvent) sgEvent:
        Event to process.
    '''

    self.writeMessage(self.formatMessage(sgEvent))

  def writeMessage(self, msg):
    '''
    Writes the msg to the handlers stream.

    Args:
      * (str) msg:
        Message to write.
    '''

    try:
      self._stream.write(msg)
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      raise

class DummyStream(object):
  @staticmethod
  def write(msg):
    pass

class SgFileEventHandler(SgStreamEventHandler):
  '''
  Event handler class that writes events to files.
  '''

  def __init__(self, filename, mode='a', delay=True):
    self.__filename = filename
    self.__filenameAbs = os.path.abspath(filename)
    self.__mode = mode

    if bool(delay):
      super(SgFileEventHandler, self).__init__(DummyStream)
    else:
      super(SgFileEventHandler, self).__init__(self._open())

  def _open(self):
    '''
    Open the file and return its object.
    '''

    return open(self.__filename, self.__mode)

  def close(self):
    '''
    Close the file the handler is writing events to.

    If the handler has yet to recieve an event this function returns
    immediately.
    '''

    with self:
      if self._stream != DummyStream:
        self.flush()

        if hasattr(self._stream, 'close'):
          self._stream.close()

        self._stream = DummyStream

      super(SgFileEventHandler, self).close()

  def filename(self):
    '''
    Returns the filename the handler is outputting events to.
    '''

    return self.__filename

  def mode(self):
    '''
    Returns the mode the log file is/will be opened with.
    '''

    return self.__mode

  def processEvent(self, sgEvent):
    '''
    Processes the event and writes a formatted string to the handlers stream.

    Args:
      * (SgEvent) sgEvent:
        Event to process.
    '''

    self.writeMessage(self, self.formatMessage(sgEvent))

class SgUDPBroadcastEventHandler(ShotgunORM.SgEventHandler):
  '''
  Event handler class that broadcasts UDP messages.
  '''

  def __init__(self, port=7479):
    super(SgUDPBroadcastEventHandler, self).__init__()
    self.__socket = self.createSocket()
    self.__port = int(port)

  def createSocket(self):
    '''
    Creates and returns a new socket object to be used by the handler.
    '''

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.setsockopt(
      socket.SOL_SOCKET,
      socket.SO_BROADCAST,
      1
    )

    return s

  def formatMessage(self, sgEvent):
    '''
    Returns a formatted string for the event.

    Subclasses can override this function to return custom msgs.

    Args:
      * (SgEvent) sgEvent:
        Event to build message for.
    '''

    event = sgEvent.event()

    msg = (
      'app=sg_monitor '
      'url=%(url)s '
      'event_type=%(event_type)s '
      'id=%(id)s '
      'created_at=%(created_at)s'
    ) % {
      'url': sgEvent.eventWatcher().connection().url(),
      'event_type': event['event_type'],
      'id': event['id'],
      'created_at': event['created_at'].isoformat('_')
    }

    return msg

  def port(self):
    '''
    Returns the port number the handler will use for broadcasting messages.
    '''

    return self.__port

  def processEvent(self, sgEvent):
    '''
    Processes the event and broadcasts a message.

    Args:
      * (SgEvent) sgEvent:
        Event to process.
    '''

    self.sendMessage(self.formatMessage(sgEvent))

  def sendMessage(self, msg):
    '''
    Send the msg using the handlers socket.

    Args:
      * (str) msg:
        Message to send.
    '''

    self.__socket.sendto(
      msg,
      ('<broadcast>', self.__port)
    )

  def socket(self):
    '''
    Returns the socket the handler uses for broadcasting messages.
    '''

    return self.__socket
