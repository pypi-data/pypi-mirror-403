from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.wait.EC import EC
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.DriverSearcher import DriverSearcher

class Querier(DriverSearcher):
  
  def __init__(self,driver):
    super().__init__(driver)
    self._ec = EC(driver)

  def query_element(self,options:AbilityOpts)->WebElement|None:
    return self._search_element(options)

  def query_elements(self,options:AbilityOpts)->list[WebElement]|None:
    return self._search_elements(options)

  def _get_element(self,options:AbilityOpts)->WebElement|None:
    '''
    Wait and Get the target WebElement
    Args:
      options (AbilityOpts): the options for querying the element
    Returns:
      WebElement|None: the first matching element or None if not found
    '''
    return self._ec.presence_of_element_located(options)

  def _get_elements(self,options:AbilityOpts)->list[WebElement]|None:
    '''
    Wait and Get the target WebElements
    Args:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None: the list of matching elements or None if not found
    '''
    return self._ec.presence_of_all_elements_located(options)