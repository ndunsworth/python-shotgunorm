
__all__ = [
  'SgAssetCreatedHandler',
  'SgHumanUserCreatedHandler',
  'SgPlaylistCreatedHandler',
  'SgProjectCreatedHandler',
  'SgProjectAssetCreatedHandler',
  'SgProjectPlaylistCreatedHandler',
  'SgProjectPublishedFileCreatedHandler',
  'SgProjectSequenceCreatedHandler',
  'SgProjectShotCreatedHandler',
  'SgProjectTaskCreatedHandler',
  'SgProjectVersionCreatedHandler',
  'SgPublishedFileCreatedHandler',
  'SgSequenceCreatedHandler',
  'SgShotCreatedHandler',
  'SgTaskCreatedHandler',
  'SgVersionCreatedHandler'
]

# Python imports
from abc import abstractmethod

# This module imports
import ShotgunORM

########################################################################
#
# Global Entity created handlers
#
########################################################################

class SgHumanUserCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgHumanUserCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgHumanUserCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgAssetCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgAssetCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgAssetCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgPlaylistCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgPlaylistCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgPlaylistCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgProjectCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgProjectCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgProjectCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgPublishedFileCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgPublishedFileCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgPublishedFileCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgSequenceCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgSequenceCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgSequenceCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgShotCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgShotCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgShotCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgVersionCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgVersionCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgVersionCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

class SgTaskCreatedHandler(ShotgunORM.SgEventHandler):
  '''

  '''

  def __init__(self):
    super(SgTaskCreatedHandler, self).__init__()

    self.addFilter(ShotgunORM.SgTaskCreatedFilter())

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

########################################################################
#
# Project specific Entity created handlers
#
########################################################################

class SgProjectAssetCreatedHandler(SgAssetCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectAssetCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectPlaylistCreatedHandler(SgPlaylistCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectPlaylistCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectPublishedFileCreatedHandler(SgPublishedFileCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectPublishedFileCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectSequenceCreatedHandler(SgSequenceCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectSequenceCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectShotCreatedHandler(SgShotCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectShotCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectTaskCreatedHandler(SgTaskCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectTaskCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project

class SgProjectVersionCreatedHandler(SgVersionCreatedHandler):
  '''

  '''

  def __init__(self, project):
    super(SgProjectVersionCreatedHandler, self).__init__()

    self._project = project

    self.addFilter(ShotgunORM.SgProjectFilter(project))

  @abstractmethod
  def processEvent(self, sgEvent):
    '''

    '''

    raise NotImplementedError()

  def project(self):
    '''

    '''

    return self._project
