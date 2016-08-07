
__all__ = [
  'SgUndo',
  'SgUndoError',
  'SgUndoAction',
  'SgUndoGroup',
  'SgUndoStackNull',
  'SgUndoStackRoot',
  'SgUndoStack'
]

import copy
import weakref

class SgUndoError(Exception):
  pass

class SgUndoAction(object):
  '''

  '''

  UNDO = 0
  REDO = 1

  def __init__(self, sgActions=[], sgResults=[]):
    self.__state = self.UNDO

    self.__actions = copy.deepcopy(sgActions)
    self.__results = copy.deepcopy(sgResult)

  def actions(self):
    '''
    Returns a list of the actions performed.
    '''

    return copy.deepcopy(self.__actions)

  def isRedoable(self):
    '''
    Returns True if the action can be performed again.

    Will only return True if the action has been undone.
    '''

    return self.__state == self.REDO

  def isUndoable(self):
    '''
    Returns True if the action can be undone.

    Will only return True if the action has not been undone.
    '''

    return self.__state == self.UNDO

  def redo(self, sgConnection):
    '''
    Performs the Shotgun actions again.

    Raises a SgUndoError if the action is not redoable.
    '''

    if self.isRedoable() == False:
      raise SgUndoError(
        'can not redo an action that has not been undone'
      )

    actions = self.__actions
    result = self.__results

    new_actions = []

    for action, result in zip(actions, results):
      action_type = action['request_type']

      if action_type == 'delete':
        new_actions.append(
          {
            'request_type': 'revive',
            'entity_type': action['entity_type'],
            'entity_id': action['entity_id']
          }
        )
      elif action_type == 'update':
        pass
        # new_actions.append(
          # {
            # 'request_type': 'update',
            # 'entity_type': action['entity_type'],
            # 'entity_id': action['entity_id'],
            # 'data': action['data']
          # }
        # )
      else:
        pass

    self.__actions = new_actions

    self.__results = sgConnection._sg_batch(new_actions)

    self.__state = self.UNDO

  def undo(self, sgConnection):
    '''
    Reverts the Shotgun actions.

    Raises a SgUndoError if the action can not be undone.
    '''

    if self.isUndoable() == False:
      raise SgUndoError(
        'can not undo an action that has already been undone'
      )

    actions = self.__actions
    result = self.__results

    new_actions = []

    for action, result in zip(actions, results):
      action_type = action['request_type']

      if action_type == 'create' or action_type == 'revive':
        new_actions.append(
          {
            'request_type': 'delete',
            'entity_type': action['entity_type'],
            'entity_id': action['entity_id']
          }
        )
      elif action_type == 'update':
        pass
      else:
        pass

    self.__actions = new_actions

    self.__results = sgConnection._sg_batch(new_actions)

    self.__state = self.REDO

  def state(self):
    '''
    Returns the undo/redo state of the action.
    '''

    return self.__state

class SgUndoStack(object):
  '''

  '''

  def __init__(self, parent=None):
    self.__undo = []
    self.__redo = []
    self.__parent = parent

  def clearRedo(self):
    '''

    '''

    self.__redo = []

  def clearUndo(self):
    '''

    '''

    self.__undo = []

  def maxUndo(self):
    '''

    '''

    return 100

  def parent(self):
    '''

    '''

    return self.__parent

  def push(self, sgUndoAction):
    '''

    '''

    if len(self.__undo) > self.maxUndo():
      self.__undo.pop(-1)

    self.__undo.insert(0, sgUndoAction)

    self.__redo = []

  def redo(self, sgConnection):
    '''

    '''

    if len(self.__redo) <= 0:
      return False

    action = self.__redo.pop(0)

    action.redo(sgConnection)

    self.__undo.insert(0, action)

    return True

  def redoSize(self):
    '''

    '''

    return len(self.__redo)

  def undo(self, sgConnection):
    '''

    '''

    if len(self.__undo) <= 0:
      return False

    action = self.__undo.pop(0)

    action.undo(sgConnection)

    self.__redo.insert(0, action)

    return True

  def undoSize(self):
    '''

    '''

    return len(self.__undo)

class SgUndoGroup(SgUndoStack):
  '''

  '''

  def __init__(self, parent=None):
    super(SgUndoGroup, self).__init__(parent)

  def redo(self, sgConnection):
    '''

    '''

    if self.redoSize() <= 0:
      return False

    while super(SgUndoGroup, self).redo(sgConnection) == True:
      pass

    return True

  def redoSize(self):
    '''

    '''

    if super(SgUndoGroup, self).redoSize() <= 0:
      return 0
    else:
      return 1

  def undo(self, sgConnection):
    '''

    '''

    if self.undoSize() <= 0:
      return False

    while super(SgUndoGroup, self).undo(sgConnection) == True:
      pass

    return True

  def undoSize(self, sgConnection):
    '''

    '''

    if super(SgUndoGroup, self).undoSize() <= 0:
      return 0
    else:
      return 1

class SgUndoStackNull(SgUndoStack):
  '''

  '''

  def __init__(self):
    super(SgUndoStackNull, self).__init__(self)

  def push(self, sgUndoAction):
    '''

    '''

    return False

  def redo(self, sgConnection):
    '''

    '''

    return False


  def undo(self, sgConnection):
    '''

    '''

    return False

class SgUndoStackRoot(SgUndoStack):
  '''

  '''

  def __init__(self):
    super(SgUndoStackRoot, self).__init__(self)

class SgUndo(object):
  '''

  '''

  def __init__(self, sgConnection, rootStack=None):
    self.__connection = weakref.ref(sgConnection)

    if rootStack == None:
      self.__root = SgUndoStackNull()
    else:
      self.__root = rootStack

    self.__stack = self.__root

  def clearRedo(self):
    '''

    '''

    self.__stack.clearRedo()

  def clearUndo(self):
    '''

    '''

    self.__stack.clearUndo()

  def connection(self):
    '''

    '''

    return self.__connection()

  def hasRedo(self):
    '''

    '''

    return self.redoSize() > 0

  def hasUndo(self):
    '''

    '''

    return self.undoSize() > 0

  def popGroup(self):
    '''

    '''

    self.__stack == self.__stack.parent()

  def push(self, sgUndoAction):
    '''

    '''

    self.__stack.push(sgUndoAction)

  def pushGroup(self):
    '''

    '''

    self.__stack.push(SgUndoGroup(self.__stack))

    self.__stack = group

  def redo(self):
    '''

    '''

    return self.__stack.redo()

  def redoSize(self):
    '''

    '''

    return self.__stack.redoSize()

  def undo(self):
    '''

    '''

    if self.__stack.undo() == False:
      self.__stack = self.__stack.parent()
    else:
      return True

  def undoSize(self):
    '''

    '''

    return self.__stack.undoSize()
