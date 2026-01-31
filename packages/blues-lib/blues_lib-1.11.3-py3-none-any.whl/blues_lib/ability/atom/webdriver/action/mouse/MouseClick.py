from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.actions.mouse_button import MouseButton
from blues_lib.ability.atom.webdriver.action.mouse.MouseBase import MouseBase
from blues_lib.types.common import AbilityOpts

class MouseClick(MouseBase):
  '''
  A representation of any pointer device for interacting with a web page.
    If the element is outside the viewable window, 
    The element will automatically roll into the window, 
    With the bottom of the element flush with the bottom of the window
  Reference: https://www.selenium.dev/documentation/webdriver/actions_api/mouse/
  '''
  def context_click(self,options:AbilityOpts)->bool:
    '''
    Context click and release
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
    Returns:
      bool : True if context click the element successfully, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.context_click(elem).perform()
    return True

  def double_click(self,options:AbilityOpts)->bool:
    '''
    Double left click
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
    Returns:
      bool : True if double click the element successfully, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.double_click(elem).perform()
    return True

  def click_and_hold(self,options:AbilityOpts)->bool:
    '''
    Click and hold
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
    Returns:
      bool : True if hold the element successfully, False otherwise 
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.click_and_hold(elem).perform()
    return True 

  def release(self,options:AbilityOpts)->bool:
    '''
    Release the hold
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
    Returns:
      bool : True if release the hold successfully, False otherwise 
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.release(elem).perform()
    return True     

  def back_click(self)->bool:
    '''
    Back to the previous page
    Returns:
      bool : True if back to the previous page successfully, False otherwise
    '''
    self._builder.pointer_action.pointer_down(MouseButton.BACK)
    self._builder.pointer_action.pointer_up(MouseButton.BACK)
    return True     
  
  def forward_click(self)->bool:
    '''
    Forward to the next page
    Returns:
      bool : True if forward to the next page successfully, False otherwise
    '''
    self._builder.pointer_action.pointer_down(MouseButton.FORWARD)
    self._builder.pointer_action.pointer_up(MouseButton.FORWARD)
    return True     



