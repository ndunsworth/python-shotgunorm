
__all__ = [
  'SgAssetCreatedFilter',
  'SgHumanUserCreatedFilter',
  'SgPlaylistCreatedFilter',
  'SgProjectCreatedFilter',
  'SgProjectFilter',
  'SgPublishedFileCreatedFilter',
  'SgSequenceCreatedFilter',
  'SgShotCreatedFilter',
  'SgTaskCreatedFilter',
  'SgVersionCreatedFilter'
]

# This module imports
import ShotgunORM

class SgAssetCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgAssetCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Asset_New'

class SgHumanUserCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgHumanUserCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_HumanUser_New'

class SgPlaylistCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgPlaylistCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Playlist_New'

class SgProjectCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgProjectCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Project_New'

class SgProjectFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self, project):
    super(SgProjectFilter, self).__init__()

    self._project = project

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.event().project == self._project

  def project(self):
    '''

    '''

    return self._project

class SgPublishedFileCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgPublishedFileCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_PublishedFile_New'

class SgSequenceCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgSequenceCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Sequence_New'

class SgShotCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgShotCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Shot_New'

class SgTaskCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgTaskCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Task_New'

class SgVersionCreatedFilter(ShotgunORM.SgEventFilter):
  '''

  '''

  def __init__(self):
    super(SgVersionCreatedFilter, self).__init__()

  def filter(self, sgEvent):
    '''

    '''

    return sgEvent.type() == 'Shotgun_Version_New'
