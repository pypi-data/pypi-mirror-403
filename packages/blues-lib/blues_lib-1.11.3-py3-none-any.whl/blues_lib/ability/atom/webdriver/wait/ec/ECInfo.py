from selenium.webdriver.support import expected_conditions 
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.wait.ec.ECBase import ECBase
from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator

class ECInfo(ECBase):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """

  def title_is(self,options:AbilityOpts)->bool:  
    '''
    Wait for the document title to be equal to a string.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the title is equal to the expected value, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.title_is(value)
    return bool(self._wait(wait_func,options))
  
  def title_contains(self,options:AbilityOpts)->bool:
    '''
    Wait for the document title to contain a substring.
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the title contains the expected substring, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.title_contains(value)
    return bool(self._wait(wait_func,options))
  
  def url_to_be(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to be equal to a string.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL is equal to the expected value, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_to_be(value)
    return bool(self._wait(wait_func,options))
  
  def url_contains(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to contain a substring.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL contains the expected substring, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_contains(value)
    return bool(self._wait(wait_func,options))

  def url_to_be(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to be equal to a string.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL is equal to the expected value, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_to_be(value)
    return bool(self._wait(wait_func,options))

  def url_contains(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to contain a substring.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL contains the expected substring, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_contains(value)
    return bool(self._wait(wait_func,options))

  def url_matches(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to match a regexp pattern.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL matches the expected pattern, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_matches(value)
    return bool(self._wait(wait_func,options))
  
  def url_changes(self,options:AbilityOpts)->bool:
    '''
    Wait for the current URL to change to a different value.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the current URL changes to a different value, False otherwise.
    '''
    value:str = options.get('value')
    wait_func = expected_conditions.url_changes(value)
    return bool(self._wait(wait_func,options))

  def text_to_be_present_in_element_value(self,options:AbilityOpts)->bool:
    '''
    Wait for the element's value contains a substring, case-sensitive.
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the value attribute contains the text, False otherwise.
    '''
    value:str = options.get('value')
    target:str = options.get('target')
    locator:tuple[str,str] = LocatorCreator.create(target)
    wait_func = expected_conditions.text_to_be_present_in_element_value(locator,value)
    return bool(self._wait(wait_func,options))

  def text_to_be_present_in_element(self,options:AbilityOpts)->bool:
    '''
    Wait for the element's text contains a substring, case-sensitive.
    Args:
      options (AbilityOpts): The options for waiting.
    Returns:
      bool: True if the text is present in the element, False otherwise.
    '''
    value:str = options.get('value')
    target:str = options.get('target')
    locator:tuple[str,str] = LocatorCreator.create(target)
    wait_func = expected_conditions.text_to_be_present_in_element(locator,value)
    return bool(self._wait(wait_func,options))
