from abc import  ABC,abstractmethod
import logging
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import ElementTarget,AbilityOpts
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class DriverSearcher(DriverAbility):
  """
  Searcher class to find elements using different strategies.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/finders/
  """
  def _search_element(self,options:AbilityOpts)->WebElement|None:
    options = self._get_ability_options(options)
    target:ElementTarget = options.get('target')

    if not target:
      return None

    if isinstance(target,WebElement):
      return target

    if isinstance(target,str):
      return self._get_element(options)

    if isinstance(target,list):
      if isinstance(target[0],WebElement):
        return target[0]

      if isinstance(target[0],str):
        # get the first matching element
        return next((elem for selector in target if (elem := self._get_element({**options,'target':selector}))), None)

    return None
  
  def _search_elements(self,options:AbilityOpts)->list[WebElement]|None:
    options = self._get_ability_options(options)
    target:ElementTarget = options.get('target')
    if not target:
      return None

    if isinstance(target,WebElement):
      return [target]

    if isinstance(target,str):
      return self._get_elements(options)

    if isinstance(target,list):
      if isinstance(target[0],WebElement):
        return target

      if isinstance(target[0],str):
        # get every selector's first matching element, not all mathing elements
        return [elem for selector in target if (elem := self._get_element({**options,'target':selector}))] or None

    return None

  @abstractmethod
  def _get_element(self,options:AbilityOpts)->WebElement|None:
    """
    Find the first element using the base webdriver method
    Parameter:
      options (AbilityOpts): the options for querying the element
    Returns:
      WebElement|None : the first element that matches the target or None if not found
    """
    pass
  
  @abstractmethod
  def _get_elements(self,options:AbilityOpts)->list[WebElement]|None:
    """
    Find all elements using the base webdriver method
    Parameter:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None : the list of elements that matches the target or None if not found
    """
    pass
