from typing import Any
import requests,time
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.ability.atom.webdriver.interaction.Alerts import Alerts
from blues_lib.types.common import AbilityOpts


class JSBase(DriverAbility):
  """
  Executes JavaScript code snippet in the current context of a selected frame or window.
  Reference : https://www.selenium.dev/documentation/webdriver/interactions/windows/#execute-script
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)

  def execute_script(self,options:AbilityOpts)->Any:
    '''
    Execute the jvascript script
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      The return value of the javascript script.
    '''
    value:str = options.get('value')
    if not value:
      return None
    args:list = options.get('args') or []
    return self._driver.execute_script(value,*args)
    
  def execute_async_script(self,options:AbilityOpts)->Any:
    '''
    Execute the javascript script asynchronously.
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      The return value of the javascript script.
    '''
    value:str = options.get('value')
    if not value:
      return None
    args:list = options.get('args') or []
    return self._driver.execute_async_script(value,*args)

  def load_and_execute_script(self,options:AbilityOpts)->Any:
    '''
    Execute the javascript script online.
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      The return value of the javascript script.
    '''
    value:str = options.get('value')
    if not value:
      return None
    response = requests.get(url = value)
    return self.execute_script({'value':response.text})
  
  def alert(self,options:AbilityOpts)->bool:
    '''
    Popup the alert dialog
    Args:
      options (AbilityOpts): the alert options
    Returns:
      None : alert return undefined in js
    '''
    options = self._get_ability_options(options)
    value:str = options.get('value')
    if not value:
      return False

    script:str = f'return alert(`{value}`);'
    self.execute_script({'value':script})

    duration:int|float = options.get('duration')
    # don't close when the duration is -1
    if duration > 0:
      time.sleep(duration)
      alerts = Alerts(self._driver)
      alerts.switch_to_alert()
      alerts.accept_alert()
    return True

  def get_document_size(self):
    script = 'return {width:document.documentElement.offsetWidth,height:document.documentElement.offsetHeight};'
    return self.execute_script({'value':script})

  def _set_document(self,options:AbilityOpts)->bool: 
    '''
    Set the document content by javascript script
    Args:
      options (AbilityOpts): the document options
    Returns:
      bool : 
    '''
    script:str = options.get('value')
    if not script:
      return False

    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False

    options = {
      'value':script,
      'args':[elem],
    }
    self.execute_script(options)
    return True

  def _set_document_for_elements(self,options:AbilityOpts)->bool: 
    script:str = options.get('value')
    if not script:
      return False

    elems:list[WebElement]|None = self._querier.query_elements(options)
    if not elems:
      return False

    options = {
      'value':script,
      'args':[elems],
    }
    self.execute_script(options)
    return True