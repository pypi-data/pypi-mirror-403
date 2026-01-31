from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions 
from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.wait.ec.ECBase import ECBase

class ECElementLocated(ECBase):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """
  
  def presence_of_element_located(self,options:AbilityOpts)->WebElement|None:
    '''
    Wait and return the first matching element to be present in the DOM.
    Args:
      options (AbilityOpts): the options for querying the element
    Returns:
      WebElement|None: return the first matching element, or return None when timeout
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    
    # has no method without _located 
    wait_func = expected_conditions.presence_of_element_located(locator)
    return self._wait(wait_func,options)

  def presence_of_all_elements_located(self,options:AbilityOpts)->list[WebElement]|None:
    '''
    Wait and return all of the matching elements in a loop query
    Args:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None: The list of WebElement instances if found, None otherwise.
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    wait_func = expected_conditions.presence_of_all_elements_located(locator)
    return self._wait(wait_func,options)

  def visibility_of_element_located(self,options:AbilityOpts)->WebElement|None:
    '''
    Wait and return the first matching element to be visible.
    Args:
      options (AbilityOpts): the options for querying the element
    Returns:
      WebElement|None: The WebElement instance if found, None otherwise.
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    wait_func = expected_conditions.visibility_of_element_located(locator)
    return self._wait(wait_func,options)
  
  def visibility_of_all_elements_located(self,options:AbilityOpts)->list[WebElement]|None:  
    '''
    Wait and return all of the matching visible elements in a loop query.
    Args:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None: The list of WebElement instances if found, None otherwise.
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    wait_func = expected_conditions.visibility_of_all_elements_located(locator)
    return self._wait(wait_func,options)

  def visibility_of_any_elements_located(self,options:AbilityOpts)->list[WebElement]|None:
    '''
    Wait and return any of the matching visible elements in a loop query.
    Args:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None: The list of WebElement instances if found, None otherwise.
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    wait_func = expected_conditions.visibility_of_any_elements_located(locator)
    return self._wait(wait_func,options)

  def invisibility_of_element_located(self,options:AbilityOpts)->bool:  
    '''
    Wait and return the state of the element to be invisible or removed.
      - The ec don't return the WebElement instance, just the state of the element.
    Args:
      options (AbilityOpts): the options for querying the element
    Returns:
      bool: True if the element is invisible or removed, False otherwise.
    '''
    target:str = options.get('target')
    locator:tuple(str,str) = LocatorCreator.create(target)
    wait_func = expected_conditions.invisibility_of_element_located(locator)
    return bool(self._wait(wait_func,options))
