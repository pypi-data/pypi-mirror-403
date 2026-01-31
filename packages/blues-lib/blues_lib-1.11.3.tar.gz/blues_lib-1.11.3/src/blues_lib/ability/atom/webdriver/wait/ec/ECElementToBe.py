from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions 
from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.wait.ec.ECBase import ECBase
from blues_lib.ability.atom.webdriver.element.Finder import Finder

class ECElementToBe(ECBase):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """

  def __init__(self,driver):
    super().__init__(driver)
    self._finder = Finder(driver)

  def element_to_be_clickable(self,options:AbilityOpts)->bool:
    '''
    Wait and return the element to be clickable.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      WebElement|None: The WebElement instance if found, None otherwise.
    '''
    target:str|WebElement = options.get('target')
    if isinstance(target,WebElement):
      elem_or_locator = target
    else:
      elem_or_locator = LocatorCreator.create(target)
    
    # this special method support two kinds of input
    # 1. WebElement instance
    # 2. locator tuple (by,value)
    wait_func = expected_conditions.element_to_be_clickable(elem_or_locator)
    return bool(self._wait(wait_func,options))

  def element_to_be_selected(self,options:AbilityOpts)->bool:
    '''
    Wait and return the element to be selected.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the element is selected, False otherwise.
    '''
    target:str|WebElement = options.get('target')
    if isinstance(target,WebElement):
      wait_func = expected_conditions.element_to_be_selected(target)
    else:
      elem_or_locator = LocatorCreator.create(target)
      wait_func = expected_conditions.element_located_to_be_selected(elem_or_locator)
    return bool(self._wait(wait_func,options))
  
  def element_to_be_stale(self,options:AbilityOpts)->bool:
    '''
    Wait and return the state of the element to be stale.
      - The ec don't return the WebElement instance, just the state of the element.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the element is stale, False otherwise.
    '''
    elem:WebElement|None = self._finder.find_element(options)
    if not elem:
      return True

    # only support WebElement instance as input
    wait_func = expected_conditions.staleness_of(elem)
    return bool(self._wait(wait_func,options))

