from typing import Any
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from blues_lib.types.common import SearchContext,ElementRoot,AbilityOpts
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator
from blues_lib.deco.ability.ECExceptionLog import ECExceptionLog

class ECBase(DriverAbility):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """

  def __init__(self,driver):
    super().__init__(driver)

  @ECExceptionLog()
  def _wait(self,wait_func,options:AbilityOpts)->Any:
    '''
    Execute the Expected Condition function and return the result
    Args:
      wait_func (function} : the ec until function
      options (AbilityOpts): the options for querying the element.
    Returns:
      Any
    '''
    options = self._get_ability_options(options)
    timeout:int|float = options.get('timeout')
    root:ElementRoot = options.get('root')
    context:SearchContext = self._get_context(root)
    result:Any = WebDriverWait(context,timeout=timeout).until(wait_func)
    if isinstance(result,list) and len(result) == 0:
      return None
    return result
  
  @ECExceptionLog()
  def _wait_root_element(self,root:str,timeout:int|float)->WebElement|None:
    locator:tuple(str,str) = LocatorCreator.create(root)
    wait_func = expected_conditions.presence_of_element_located(locator)
    return WebDriverWait(self._driver,timeout=timeout).until(wait_func)

  def _get_context(self,root:ElementRoot,timeout:int=5)->SearchContext:
    '''
    Find and return the element root, contains 3 kinds of root:
    1. WebElement: return the element
    2. WebDriver: return the driver 
    3. ShadowRoot: return the shadow root 
    '''
    if not root:
      return self._driver
    if isinstance(root,SearchContext):
      return root
    elem:WebElement|None = self._wait_root_element(root,timeout)
    if not elem:
      return self._driver
    return elem.shadow_root if self._is_shadow_host(elem) else elem
