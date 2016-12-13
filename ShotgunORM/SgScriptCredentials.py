
__all__ = [
  'SgScriptCredentials'
]

class SgScriptCredentials(object):
  '''

  '''

  def __repr__(self):
    return '<SgScriptCredentials(name: "%s", version: "%s")>' % (
      self.name(),
      self.version()
    )

  def __init__(
    self,
    sgSite,
    sgScriptName,
    sgScriptKey,
    sgScriptVersion='1.0'
  ):
    self.__site = sgSite
    self.__name = str(sgScriptName)
    self.__key = str(sgScriptKey)
    self.__version = str(sgScriptVersion)

  def key(self):
    '''

    '''

    return self.__key

  def name(self):
    '''

    '''

    return self.__name

  def site(self):
    '''

    '''

    return self.__site

  def version(self):
    '''

    '''

    return self.__version
