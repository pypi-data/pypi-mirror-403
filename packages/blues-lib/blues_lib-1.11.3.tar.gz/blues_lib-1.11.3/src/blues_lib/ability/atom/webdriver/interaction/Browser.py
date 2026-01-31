from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class Browser(DriverAbility):
  """
  Working with browser
  Reference : https://www.selenium.dev/documentation/webdriver/interactions/browser/
  """

  def get_title(self)->str:
    '''
    Get the browser document's title
    Returns:
      str
    '''
    return self._driver.title

  def get_current_url(self)->str:
    '''
    Get the current page url
    Returns:
      str
    '''
    return self._driver.current_url

  def get_page_source(self)->str:
    '''
    Get the current page source
    Returns:
      str
    '''
    return self._driver.page_source
