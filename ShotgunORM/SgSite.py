
__all__ = [
  'SgSite'
]

# Python imports
import webbrowser

# This module imports
import ShotgunORM

class SgSite(object):
  '''

  '''

  def __eq__(self, item):
    if isinstance(item, SgSite):
      return item._url == self.url
    else:
      return False

  def __repr__(self):
    return '<SgSite("%s")>' % (
      self.url()
    )

  def __init__(self, sgUrl):
    self._url = sgUrl
    self._name = ShotgunORM.facilityNameFromUrl(sgUrl)

  def isStaging(self):
    '''

    '''

    return self._name.endswith('-staging')

  def name(self):
    '''

    '''

    return self._name

  def url(self, openInBrowser=False):
    '''
    Returns the Shotgun url for the site.

    Args:
      * (bool) openInBrowser:
        When True opens the URL in the operating systems default
        web-browser.
    '''

    if openInBrowser:
      webbrowser.open(self._url)
    else:
      return self._url
