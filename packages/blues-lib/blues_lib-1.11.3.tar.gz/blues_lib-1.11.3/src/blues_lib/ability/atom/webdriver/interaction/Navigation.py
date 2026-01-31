from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class Navigation(DriverAbility):
  """
  Working with navigation
  Reference : https://www.selenium.dev/documentation/webdriver/interactions/navigation/
  """

  def back(self)->bool:
    '''
    Back to the prev page
    Returns:
      bool: True if the page is back successfully, False otherwise
    '''
    try:
      self._driver.back()
      return True
    except Exception as e:
      return False
  
  def forward(self)->bool:
    '''
    Forward to the next page
    Returns:
      bool: True if the page is forward successfully, False otherwise       
    '''
    try:
      self._driver.forward()
      return True
    except Exception as e:
      return False
  
  def refresh(self)->bool:
    '''
    Refresh to the current page
    Returns:
      bool: True if the page is refresh successfully, False otherwise
    '''
    try:
      self._driver.refresh()
      return True
    except Exception as e:
      return False
  