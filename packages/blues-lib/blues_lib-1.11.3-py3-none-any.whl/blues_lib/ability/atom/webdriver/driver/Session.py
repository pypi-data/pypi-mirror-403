from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.ability.atom.webdriver.interaction.JavaScript import JavaScript
from blues_lib.types.common import AbilityOpts

class Session(DriverAbility):
  """
  Working with session
  Reference : https://www.selenium.dev/documentation/webdriver/drivers/
  """

  def open(self,options:AbilityOpts)->bool: 
    status = self.get(options)
    if not status:
      return False
    
    style:dict|str = options.get('style')
    if style:
      javascript = JavaScript(self._driver)
      javascript.set_head_style({'value':style})

    return True
      
  def get(self,options:AbilityOpts)->bool: 
    '''
    Open a page
    Args:
      options (AbilityOpts): the options
        - value (str): The url to open
    Returns:
      bool: True if the page is opened successfully, False otherwise
    '''
    url:str = options.get('value','')
    try:
      self._driver.get(url)
      return True        
    except Exception as e:
      return False

  def close(self)->bool:
    '''
    Close the current window or tab
    If only one window/tab ,the browser will be closed
    Returns:
      bool: True if the window is closed successfully, False otherwise
    '''
    try:
      self._driver.close()
      return True
    except Exception as e:
      return False

  def quit(self)->bool:
    '''
    Close all windows and tabs
    Returns:
      bool: True if the browser is closed successfully, False otherwise
    '''
    try:
      self._driver.quit()
      return True
    except Exception as e:
      return False

  def get_log(self)->list:
    '''
    Get the log of the current session
    Returns:
      list: A list of log entries.
    '''
    return self._driver.get_log("browser")

  def is_driver_available(self)->bool:
    '''
    Whether the current driver is available
    Returns:
      bool 
    '''
    try:
      self._driver.current_url
      return True
    except Exception as e:
      return False
