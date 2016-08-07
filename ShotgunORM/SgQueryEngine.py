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
  'SgQueryEngine'
]

# Python imports
import threading
import weakref

# This module imports
import ShotgunORM

class SgQueryJob(object):
  '''

  '''

  def __repr__(self):
    eIds = []

    for entity in self.entities():
      e = entity()

      if e == None:
        continue

      eIds.append(e.id)

    return '<%s(type:%s, fields:%s, entities:%s)>' % (
      type(self).__name__,
      self.entityType(),
      self.fields(),
      eIds
    )

  def __lt__(self, item):
    return self.fields() < item.fields()

  def __gt__(self, item):
    return self.fields() > item.fields()

  def __eq__(self, item):
    return self.fields() == item.fields()

  def __init__(self, sgEntityType, sgEntities, sgFields):
    self._entityType = sgEntityType
    self._entities = set(sgEntities)
    self._fields = set(sgFields)

  def fields(self):
    return self._fields

  def entities(self):
    return self._entities

  def entityType(self):
    return self._entityType

class SgQueryEngine(object):
  '''
  Class that represents an asynchronous Entity field value pulling engine.
  '''

  def __del__(self):
    try:
      self.shutdown()
    except:
      pass

  def __enter__(self):
    self.__lock.acquire()

  def __exit__(self, exc_type, exc_value, traceback):
    self.__lock.release()

    return False

  def __repr__(self):
    connection = self.connection()

    if connection == None:
      return '<SgQueryEngine>'

    return '<SgQueryEngine(url:"%(url)s", script:"%(script)s">' % {
      'url': connection.url(),
      'script': connection.scriptName()
    }

  def __init__(self, sgConnection):
    self.__lock = threading.Lock()
    self.__block = threading.RLock()
    self._qEvent = threading.Event()
    self._qShutdownEvent = threading.Event()

    self._qEvent.clear()

    self.__connection = weakref.ref(sgConnection)

    self._pendingQueries = []
    self._entityQueue = {}

    self.__engineThread = threading.Thread(
      name=self.__repr__(),
      target=SgQueryEngineWorker,
      args = [
        self.__connection,
        self.__lock,
        self.__block,
        self._qEvent,
        self._qShutdownEvent,
        self._entityQueue,
        self._pendingQueries
      ]
    )

    self.__engineThread.setDaemon(True)

  def addQueue(self, sgEntity, sgFields):
    '''
    Adds the passed Entity and the specified fields to the queue.
    '''

    # The field pull queue works by taking the fields that each Entity is asking
    # to pull and batches them in alike groups minimizing the amount of passes
    # the Shotgun database will need to return each Entity by type.
    #
    # Each time a new batch is added the currently pending pulls are locked and
    # checked to see if the new batch items can be added to them.  This means a
    # late addition may return quicker then another item that was added to the
    # queue ealier simply because its requesting a set of fields that are lower
    # in the queue.
    #
    # Example 1:
    #
    #   * ENTITY: FIELDS PULLING *
    #   Entity A: ['firstname', 'lastname']
    #   Entity B: ['firstname', 'lastname', 'created_by']
    #   Entity C: ['firstname, 'lastname', 'created_by', 'created_at']
    #
    #   * BATCH: ENTITIES, FIELDS PULLING *
    #   Batch1: [A, B, C], ['firstname', 'lastname']
    #   Batch2: [B, C], ['created_by']
    #   Batch3: [C], ['created_at']

    if not isinstance(sgEntity, ShotgunORM.SgEntity):
      raise TypeError('expected an SgEntity got %s' % sgEntity)

    if not self.__engineThread.isAlive():
      raise RuntimeError('engine thread is not running')

    try:
      undoFields = []
      pullFields = []

      sgFields = set(sgFields)

      for name, field in sgEntity.fields(sgFields).items():
        pullFields.append(name)

        # Mark the field that it is updating.
        field._SgField__isUpdatingEvent.clear()

        undoFields.append(field)

      if len(pullFields) <= 0:
        return

      ShotgunORM.LoggerQueryEngine.debug('%(qEng)s.addQueue(...)', {'qEng': self})
      ShotgunORM.LoggerQueryEngine.debug('    * sgEntity: %(sgEntity)s', {'sgEntity': sgEntity})
      ShotgunORM.LoggerQueryEngine.debug('    * sgFields: %(sgFields)s', {'sgFields': pullFields})

      with self:
        pullFields = set(pullFields)

        eq = None

        t = sgEntity.type

        if self._entityQueue.has_key(t):
          eq = self._entityQueue[t]
        else:
          eq = []

          self._entityQueue[t] = eq

        valid = False

        eqLen = len(eq)

        if eqLen <= 0:
          # Weakref the Entity, this allows the Engine to not keep Entities
          # around.
          entities = [weakref.ref(sgEntity)]

          q = SgQueryJob(t, entities, pullFields)

          eq.append(q)

          self._pendingQueries.append(q)

          valid = True
        elif eqLen == 1:
          # This check sees if the q for this Entity type contains only a
          # single Entity and if so it sees if that Entity is the currently
          # processing one.  If so it merges the q's fields with the current
          # list of fields for the Entity.

          q = eq[0]
          qEntities = q.entities()

          if len(qEntities) == 1:
            qEntity = list(qEntities)[0]()

            if qEntity == sgEntity:
              q.fields().update(pullFields)

              valid = True

        if not valid:
          for q in eq:
            qFields = q.fields()

            # Skip when the current batch has more fields to query then the
            # Entity is asking for.
            if len(pullFields) < len(qFields):
              continue

            sharedFields = pullFields & qFields

            if len(sharedFields) >= 1:
              q.entities().add(
                weakref.ref(sgEntity)
              )

              pullFields -= sharedFields

            # Halt if all fields have been queued up!
            if len(pullFields) <= 0:
              break

          if len(pullFields) >= 1:
            entities = [weakref.ref(sgEntity)]

            q = SgQueryJob(t, entities, pullFields)

            eq.append(q)

            self._pendingQueries.append(q)

        # Un-lock the engine if the q was empty.
        # if not self._qEvent.isSet():
        self._qEvent.set()

        # Sort the field q list so that the largest queries are first.
        eq.sort(reverse=True)
    except Exception, e:
      ShotgunORM.LoggerQueryEngine.error(e)

      for field in undoFields:
        field._SgField__isUpdatingEvent.set()

      raise

  def block(self):
    '''
    Blocks the query engine.

    This allows multiple Entities to be batch added and prevents engine from
    prematurely processing results.

    Note:
      You must always make sure to call unblock() after you are finished adding
      items to the queue.  Even if your code raises and exception you must not
      forget to unblock the engine.
    '''

    self.__block.acquire()

  def connection(self):
    '''
    Returns the connection the engine belongs to.
    '''

    return self.__connection()

  def isBlocking(self):
    '''
    Returns True if the engine is currently blocking.
    '''

    return self.__block._is_owned()

  def pending(self):
    '''
    Returns the number of pending queries.
    '''

    return len(self._pendingQueries)

  def shutdown(self):
    '''
    Shutdown the engine.
    '''

    if self.__engineThread.isAlive():
      self._qEvent.set()
      self._qShutdownEvent.wait()

  def start(self):
    '''
    Starts the engines background thread.
    '''

    self.__engineThread.start()

  def unblock(self):
    '''
    Un-blocks the query engine.

    Note:
      This must always be called after blocking the engine.
    '''

    self.__block.release()

def SgQueryEngineWorker(
  connection,
  lock,
  block,
  event,
  eventShutdown,
  entityQueue,
  pendingQueries
):
  ##############################################################################
  #
  # IMPORTANT!!!!!
  #
  # You must make sure to delete any var that is created which points to an
  # Entity object. Otherwise the worker wont let it fall out of scope and this
  # will prevent the Entity from being gc'd.
  #
  ##############################################################################

  while True:
    entityType = None
    entityFields = None
    entities = None

    event.wait()

    if len(pendingQueries) <= 0:
      try:
        ShotgunORM.LoggerQueryEngine.debug(
          'Stopping because engine set event and pendingQueries size is zero'
        )
      except:
        pass

      eventShutdown.set()

      return

    with block:
      q = pendingQueries.pop(0)

      qSize = len(pendingQueries) + 1

      ShotgunORM.LoggerQueryEngine.debug('Queue: job 1 of %(size)d', {'size': qSize})

    with lock:
      if len(pendingQueries) <= 0:
        event.clear()

      entityType = q.entityType()
      entityFields = list(q.fields())
      entities = list(q.entities())

      entityQueue[entityType].remove(q)

      ShotgunORM.LoggerQueryEngine.debug('Preparing to process job %(q)s', {'q': q})

    entityList = {}
    entityIds = []

    for i in entities:
      entity = i()

      # Check it was gc'd!
      if entity == None:
        continue

      try:
        entityList[entity['id']] = entity

        entityIds.append(entity['id'])
      finally:
        del entity

    # Bail if all the Entities were gc'd!
    if len(entityList) <= 0:
      ShotgunORM.LoggerQueryEngine.debug('Skipping job all Entities no longer exist')

      continue

    ShotgunORM.LoggerQueryEngine.debug('    * Processing')

    con = connection()

    if con == None:
      try:
        ShotgunORM.LoggerQueryEngine.debug(
          '    * Stopping because connection not found'
        )
      except:
        pass

      return

    try:
      ShotgunORM.LoggerQueryEngine.debug('    * Searching')

      sgSearch = None

      if len(entityIds) == 1:
        sgSearch = con._sg_find(entityType, [['id', 'is', entityIds[0]]], entityFields)
      else:
        sgSearch = con._sg_find(entityType, [['id', 'in', entityIds]], entityFields)

      ShotgunORM.LoggerQueryEngine.debug('    * Searching complete!')
    except Exception, e:
      ShotgunORM.LoggerQueryEngine.error(e)

      for entity in entityList.values():
        for field in entity.fields(entityFields).values():
          field._SgField__isUpdatingEvent.set()

        del entity

      del entityList

      continue
    finally:
      del con

    for result in sgSearch:
      entity = entityList[result['id']]

      del result['type']

      try:
        for fieldName, field in entity.fields(entityFields).items():
          field.setSyncUpdate(result[fieldName])

          field._SgField__isUpdatingEvent.set()
      finally:
        del entity

    del entityList

    eventShutdown.set()

    try:
      ShotgunORM.LoggerQueryEngine.debug('    * Processing complete!')
    except:
      pass
