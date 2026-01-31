from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.action.mouse.MouseBase import MouseBase
from blues_lib.types.common import AbilityOpts

class MouseMove(MouseBase):
  
  def move_to_element(self,options:AbilityOpts)->bool:
    '''
    Moves the mouse to the in-view center point of the element
    If the element outside in the viewport, it will move into the viewport automatically
    Automaic moving : the element's bottom border align to the window's bottom border
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
    Returns:
      bool : True if move the mouse successfully, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.move_to_element(elem).perform()
    return True

  def move_to_element_with_offset(self,options:AbilityOpts)->bool:
    '''
    Offset form the element
    This method moves the mouse to the in-view center point of the element, 
    Then moves by the provided offset.
     - if the offset pointer out of the view, will throw exception
    Args:
      options (AbilityOpts): The element to select.
        - options['target'] (ElementTarget) : the element to click
        - options['value'] (tuple[int,int]) : the offset value x,y , e.g. (10, 10)
    Returns:
      bool : True if move the mouse successfully, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    value:tuple[int,int] = options.get('value') or (0,0)
    if not elem:
      return False
    self._chains.move_to_element_with_offset(elem,*value).perform()
    return True

  def move_to_location(self,options:AbilityOpts)->True:
    '''
    Offset from Viewport
    The viewport's top left point to the element's center point (not the element's top left point)
    Test with hold
    Args:
      options (AbilityOpts): The element to select.
        - options['value'] (tuple[int,int]) : the offset value, e.g. (10, 10)
    Returns:
      bool : True if move the mouse successfully, False otherwise
    '''
    value:tuple[int,int] = options.get('value') or (0,0)
    self._builder.pointer_action.move_to_location(*value)
    self._builder.perform()
    return True

  def move_by_offset(self,options:AbilityOpts)->True:
    '''
    Offset from Viewport
    This method moves the mouse from its current position by the offset provided by the user. 
    Test with hold
    Args:
      options (AbilityOpts): The element to select.
        - options['value'] (tuple[int,int]) : the offset value, e.g. (10, 10)
    Returns:
      bool : True if move the mouse successfully, False otherwise
    '''
    value:tuple[int,int] = options.get('value') or (0,0)
    self._chains.move_by_offset(*value).perform()
    return True

