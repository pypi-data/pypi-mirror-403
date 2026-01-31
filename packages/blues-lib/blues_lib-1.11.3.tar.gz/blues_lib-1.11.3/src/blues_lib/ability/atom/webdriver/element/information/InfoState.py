from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.element.information.InfoBase import InfoBase
from blues_lib.types.common import AbilityOpts

class InfoState(InfoBase):

  def is_present(self,options:AbilityOpts)->bool:
    '''
    Check if the connected Element is in the document
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      bool : return True if the element is presence, otherwise False
    '''
    return True if self._querier.query_element(options) else False

  def is_displayed(self,options:AbilityOpts)->bool:
    '''
    Check if the connected Element is displayed on a webpag
      - not defined by the w3c specification
      - relies on executing a large JavaScript function directly
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      bool : return True if the element is displayed, otherwise False
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.is_displayed() if elem else False

  def is_enabled(self,options:AbilityOpts)->bool:
    '''
    If the connected Element is enabled or disabled on a webpage
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      bool : return True if the element is enabled, otherwise False
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.is_enabled() if elem else False

  def is_selected(self,options:AbilityOpts)->bool:
    '''
    Check if the connected Element is selected or not, widely used on:
      1. check box
      2. radio box
      3. input element
      4. option element
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      bool : return True if the element is selected, otherwise False
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.is_selected() if elem else False
