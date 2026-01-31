from selenium.webdriver.support import expected_conditions 
from selenium.webdriver.common.alert import Alert

from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.wait.ec.ECBase import ECBase

class ECSwitch(ECBase):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """

  def number_of_windows_to_be(self,options:AbilityOpts)->bool:
    '''
    Wait for the number of windows to change to `value`
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the number of windows is equal to the expected value, False otherwise.
    '''
    value:int = options.get('value')
    wait_func = expected_conditions.number_of_windows_to_be(value)
    return bool(self._wait(wait_func,options))
  
  def new_window_is_opened(self,options:AbilityOpts)->bool:
    '''
    Wait for new tab/window is opened, only case about the handle's count , don't case the handle's value.
    Args:
      value (list[str]): the current existing handles list
      wait_time (WaitTime|None, optional): The waiting time. Defaults to None.
    Returns:
      bool: True if the new windows are opened, False otherwise.
    '''
    value:list[str] = options.get('value')
    wait_func = expected_conditions.new_window_is_opened(value)
    return bool(self._wait(wait_func,options))
  
  def alert_is_present(self,options:AbilityOpts|None=None)->Alert|None:
    '''
    Wait for the alert to be present.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      Alert|None: The alert object if present, None otherwise.
    '''
    wait_func = expected_conditions.alert_is_present()
    return self._wait(wait_func,options)

  def frame_to_be_available_and_switch_to_it(self,options:AbilityOpts)->bool:
    '''
    Wait and switch to the frame
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the frame is switched, False otherwise.
    '''
    target:str = options.get('target')
    locator:tuple[str,str] = LocatorCreator.create(target)

    wait_func = expected_conditions.frame_to_be_available_and_switch_to_it(locator)
    return bool(self._wait(wait_func,options))
     
