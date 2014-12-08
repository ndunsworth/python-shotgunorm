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
  'SgEvent',
  'SgEventFilter',
  'SgEventFilterer',
  'SgEventHandler',
  'SgEventWatcher',
]

# Python imports
import threading

# This module imports
import ShotgunORM

class DummyStream(object):
  @staticmethod
  def write(msg):
    pass

class SgEvent(object):
  '''
  Class that represents a Shotgun Event retrieved by a SgEventWatcher.
  '''

  def __init__(self, sgEventMonitor, sgEvent):
    self.__monitor = sgEventMonitor
    self.__event = sgEvent

  def event(self):
    '''
    Returns the events Entity object.
    '''

    return self.__event

  def eventWatcher(self):
    '''
    Returns the SgEventWatcher that retrieved the event.
    '''

    return self.__monitor

  def type(self):
    '''
    Returns the EventLogEntry event_type.
    '''

    return self.__event['event_type']

class SgEventFilter(object):
  '''
  Class used by SgEventHandlers.
  '''

  def __init__(self):
    pass

  def filter(self, sgEvent):
    '''
    Returns True if the EventLogEntry should be processed.

    Subclasses can implement this to filter for specific events.

    Args:
      * (SgEvent) sgEvent:
        Event to filter.
    '''

    return True

class SgEventFilterer(object):
  '''
  Class which stores a list of SgEventFilter objects and filters SgEvents.
  '''

  def __init__(self):
    self.__filters = set([])

  def addFilter(self, sgFilter):
    '''
    Adds the SgEventFilter to the list of filters the filterer contains.

    Args:
      * (SgEventFilter) sgFilter:
        Filter to add.
    '''

    self.__filters.add(sgFilter)

  def filter(self, sgEvent):
    '''
    Returns True if the event passes any of the SgEventFilter objects the
    filterer contains.

    Args:
      * (SgEvent) sgEvent:
        Event to filter.
    '''

    if len(self.__filters) > 0:
      for i in self.__filters:
        if i.filter(sgEvent):
          return True

      return False

    return True

  def filters(self):
    '''
    Returns the list of SgEventFilters the filterer contains.
    '''

    return list(self.__filters)

  def removeFilter(self, sgFilter):
    '''
    Removes the SgEventFilter from the list of filters the filterer contains.

    Returns True if the filter was removed.

    Args:
      * (SgEventFilter) sgFilter:
        Filter to remove.
    '''

    try:
      self.__filters.remove(sgFilter)

      return True
    except ValueError:
      return False

class SgEventHandler(SgEventFilterer):
  '''
  Class SgEventWatchers use to handle SgEvents.
  '''

  def __enter__(self):
    self.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.release()

    return False

  def __init__(self):
    super(SgEventHandler, self).__init__()

    self.__lock = self.createLock()

  def acquire(self):
    '''
    Acquires the handlers lock.
    '''

    if self.__lock:
      self.__lock.acquire()

  def close(self):
    '''
    Close up any resources used by the handler.

    Subclasses should ensure this gets called from overridden methods.
    '''

    pass

  def createLock(self):
    '''
    Creates a lock object that will be used by the handler to serialize access
    to underlying I/O functionality which may not be thread safe.
    '''

    return threading.Lock()

  def flush(self):
    '''
    Ensure all I/O output has been flushed.

    Default function does nothing.
    '''

    pass

  def handleError(self, sgEvent, exception):
    '''
    Handle an error that occured during handleEvent().

    Default action re-raises the exception.
    '''

    raise exception

  def handleEvent(self, sgEvent):
    '''
    Handles a SgEvent generated by the worker thread.

    If filter(sgEvent) returns True then processEvent(sgEvent) is called to
    process the event.

    Args:
      * (SgEvent) sgEvent:
        Event to handle.
    '''

    if self.filter(sgEvent):
      with self:
        try:
          self.processEvent(sgEvent)

          return True
        except Exception, e:
          self.handleError(sgEvent, sgEvent)
        finally:
          return False

    return False

  def processEvent(self, sgEvent):
    '''
    Process the event.

    Default function raises NotImplementedError.

    Args:
      * (SgEvent) sgEvent:
        Event to process.
    '''

    raise NotImplementedError()

  def release(self):
    '''
    Releases the handlers lock.
    '''

    if self.__lock:
      self.__lock.release()

class SgEventWatcher(SgEventFilterer):
  '''
  Class that monitors EventLogEntrys.
  '''

  NO_EVENT = -3
  LAST_EVENT = -2
  FIRST_EVENT = -1

  UPDATE_INTERVAL_MIN = 2

  def __del__(self):
    self.stop()

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

    return False

  def __repr__(self):
    return '<SgEventWatcher(connection=%(connection)s>' % {
      'connection': self.connection(),
    }

  def __init__(
    self,
    sgConnection,
    startProcessingAtId=None,
    updateInterval=10
  ):
    super(SgEventWatcher, self).__init__()

    self.__lock = threading.RLock()
    self.__connection = sgConnection
    self.__handlers = []
    self.__updateInterval = int(updateInterval)

    if self.__updateInterval < self.UPDATE_INTERVAL_MIN:
      self.__updateInterval = self.UPDATE_INTERVAL_MIN

    if startProcessingAtId == None:
      startProcessingAtId = self.LAST_EVENT
    elif startProcessingAtId < self.NO_EVENT:
      startProcessingAtId = self.NO_EVENT

    self.__aborted = False
    self.__running = False
    self.__lastEvent = None
    self.__threadData = {
      'event': threading.Event(),
      'start_at_id': startProcessingAtId,
      'batch_size': self.batchSize()
    }

    self.__monitorThread = None

  def aborted(self):
    '''
    Returns True if the watcher has been instructed to stop operation.

    This is used by the worker thread of the watcher to determine if it should
    halt monitoring for events.
    '''

    return self.__aborted

  def addHandler(self, sgEventHandler):
    '''
    Adds the SgEventHandler to the list of handlers the watcher contains.

    Args:
      * (SgEventHandler) sgEventHandler:
        Handler to add.
    '''

    with self:
      handlers = list(self.__handlers)

      handlers.append(sgEventHandler)

      self.__handlers = handlers

  def batchSize(self):
    '''
    The number of entries to retrieve per batch.

    When the worker thread queries Shotgun for events it does so in batches
    of this size.
    '''

    return 250

  def connection(self):
    '''
    Returns the SgConnection the watcher uses for communicating with Shotgun.
    '''

    return self.__connection

  def handlers(self):
    '''
    Returns a list of all the SgEventHandlers the watcher contains.
    '''

    return list(self.__handlers)

  def isRunning(self):
    '''
    Returns True if the watcher is running and monitoring Shotgun for events
    '''

    return self.__running

  def isWatching(self):
    '''
    See isRunning().
    '''

    return self.isRunning()

  def logger(self):
    '''
    Returns the logger used by the watcher.
    '''

    return ShotgunORM.LoggerEventWatcher

  def lastEvent(self):
    '''
    Returns the last processed SgEvent.
    '''

    return self.__lastEvent

  def processEvent(self, sgEventLogEntry):
    '''
    Processes the EventLogEntry.

    Args:
      * (SgEntity) sgEventLogEntry:
        Event to process.
    '''

    sgEvent = SgEvent(self, sgEventLogEntry)

    if len(self.__handlers) < 1 or not self.filter(sgEvent):
      return False

    handled = 0

    for handler in self.__handlers:
      try:
        handled += handler.handleEvent(sgEvent)
      except Exception, e:
        self.logger().error(str(e))

    self.__lastEvent = sgEventLogEntry

    return (handled > 0)

  def removeHandler(self, sgEventHandler):
    '''
    Removes the SgEventHandler from the list of handlers the watcher contains.

    Returns True if the handler was removed.

    Args:
      * (SgEventHandler) sgEventHandler:
        Handler to add.
    '''

    result = True

    with self:
      handlers = list(self.__handlers)

      try:
        handlers.remove(handler)

        self.__handlers = handlers
      except ValueError:
        result = False

    return result

  def setBeginProcessingAt(self, idNumber):
    '''
    Sets the EventLogEntry Entity ID that monitoring will start at.

    If the watcher is already running when this function is called a
    RuntimeERror will be raised.

    Args:
      * (int) idNumber:
        ID that monitoring will start.

        SgEventWatcher.NO_EVENT - no prev events only new ones.
        SgEventWatcher.LAST_EVENT - the last EventLogEntry in the database.
        SgEventWatcher.FIRST_EVENT - all events in the Shotgun database.
    '''

    if idNumber == None:
      idNumber = self.LAST_EVENT
    elif idNumber < self.NO_EVENT:
      idNumber = self.NO_EVENT

    with self:
      if self.isRunning():
        raise RuntimeError(
          (
            'event watcher is already running, unable to set the first event '
            'id to process'
          )
         )

      self.__threadData['start_at_id'] = idNumber

  def setUpdateInterval(self, secs):
    '''
    Sets the update interval that Shotgun will be queried for new events.

    If the event watcher is already running then the new interval will be used
    after the next batch is processed.

    Args:
      * (int) secs:
        Interval in seconds.
    '''

    secs = int(secs)

    if secs < self.UPDATE_INTERVAL_MIN:
      secs = self.UPDATE_INTERVAL_MIN

    self.__updateInterval = secs

  def start(self):
    '''
    Starts the event watcher, if already started returns immediately.
    '''

    with self:
      if self.isRunning():
        return

      self.logger().debug('start')

      self.__running = True

      self.__monitorThread = threading.Thread(
        name=self.__repr__(),
        target=SgEventWatcherWorker,
        args = [
          self,
          self.__threadData
        ]
      )

      self.__monitorThread.setDaemon(True)

      self.__monitorThread.start()

  def _workerFinished(self):
    '''
    Internal!
    '''

    self.__threadData['event'].clear()

    if self.__lastEvent != None:
      self.__threadData['start_at_id'] = self.__lastEvent['id'] + 1

    self.__aborted = False
    self.__running = False

  def stop(self):
    '''
    Stops the event watcher, if not running returns immediately.
    '''

    thread = None

    with self:
      if not self.isRunning():
        return

      self.logger().debug('stop')

      thread = self.__monitorThread

      self.__aborted = True

      self.__threadData['event'].set()

    thread.join()

  def updateInterval(self):
    '''
    Returns the update interval that Shotgun will be queried for new events.

    Value is in seconds.
    '''

    return self.__updateInterval

def SgEventWatcherWorker(monitor, threadData):
  '''
  Worker thread used by SgEventWatcher to monitor Shotgun for events.
  '''

  e = threadData['event']

  connection = monitor.connection()
  logger = monitor.logger()

  lastId = threadData['start_at_id']

  if lastId < 0:
    if lastId == monitor.FIRST_EVENT:
      pass
    else:
      lastEvent = connection.findOne(
        'EventLogEntry',
        [],
        order=[
          {
            'field_name': 'id',
            'direction': 'desc'
          }
        ]
      )

      if lastEvent:
        lastId = lastEvent['id']

        if lastId == monitor.LAST_EVENT:
          lastId -= 1
      else:
        lastId = -1
  else:
    lastId -= 1

  order=[{'field_name':'id','direction':'asc'}]
  limit = threadData['batch_size']
  eventBuffer = []

  while True:
    logger.debug(
      'retrieving events starting at id %(id)s' % {
        'id': lastId + 1
      }
    )

    if monitor.aborted():
      monitor._workerFinished()

      return

    e.wait(monitor.updateInterval())

    events = []
    page = 0

    while True:
      if monitor.aborted():
        monitor._workerFinished()

        return

      try:
        eventBuffer = connection.find(
          'EventLogEntry',
          [
            [
              'id',
              'greater_than',
              lastId
            ]
          ],
          order=order,
          page=page,
          limit=limit
        )
      except (
        ShotgunORM.SHOTGUN_API.ProtocolError,
        ShotgunORM.SHOTGUN_API.ResponseError,
        socket.error
      ), e:
        logger.warn(str(e))

        continue

      events.extend(eventBuffer)

      if len(eventBuffer) < limit:
        break

      page += 1

    with monitor:
      for i in events:
        monitor.processEvent(i)

    if len(events) > 0:
      lastId = events[-1]['id']

    logger.debug(
      'retrieved %(count)s events' % {
        'count': len(events)
      }
    )
