from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.action.mouse.MouseBase import MouseBase
from blues_lib.types.common import AbilityOpts

class MouseDrag(MouseBase):
  '''
  These methods first move the mouse to the designated origin and then by the number of pixels in the provided offset. Note that the position of the mouse must be in the viewport or else the command will error.
  Reference: https://www.selenium.dev/documentation/webdriver/actions_api/mouse/#move-by-offset
  '''
  
  def drag_and_drop(self,options:AbilityOpts)->bool:
    '''
    Darg the draggable into the droppable
    The centers of the two elements will coincide
    Args:
      options {AbilityOpts} : The element query options
    Returns:
      bool : True if the element is found and moved, False otherwise
    '''
    draggable,droppable = self._get_draggable_and_droppable(options)
    if not droppable or not draggable:
      return False
    self._chains.drag_and_drop(draggable,droppable).perform()
    return True

  def drag_and_drop_by_offset(self,options:AbilityOpts)->bool:
    '''
    Move relative to the current position
    Args:
      options {AbilityOpts} : The element query options
    Returns:
      bool : True if the element is found and moved, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    value:list[int] = options.get('value')
    if not elem or not value:
      return False
    self._chains.drag_and_drop_by_offset(elem,*value).perform()
    return True

  def drag_to_element_with_offset(self,options:AbilityOpts)->bool:
    '''
    The distance between the two elements's centers
    Args:
      options {AbilityOpts} : The element query options
    Returns:
      bool : True if the element is found and moved, False otherwise
    '''
    draggable,droppable = self._get_draggable_and_droppable(options)
    value:list[int] = options.get('value')
    if not droppable or not draggable or not value:
      return False
    self._chains.click_and_hold(draggable).move_to_element_with_offset(droppable,*value).release(draggable).perform()
    return True

  def drag_to_location(self,options:AbilityOpts)->bool:
    '''
    Move to a point relative to the viewport's top left point
    Use the new feature -- ActionBuilder
    Args:
      options {AbilityOpts} : The element query options
    Returns:
      bool : True if the element is found and moved, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    value:list[int] = options.get('value')
    if not elem or not value:
      return False
    self._chains.click_and_hold(elem).perform()
    self._builder.pointer_action.move_to_location(*value)
    self._builder.perform()
    self._chains.release(elem).perform()        
    return True

  def drag_to_border(self,options:AbilityOpts)->bool:
    '''
    Darg a element to a target container's border
    经测试不准确，需进一步优化
    Args:
      options {AbilityOpts} : The element query options
    Returns:
      bool : True if the element is found and moved, False otherwise
    '''
    drag_opts:AbilityOpts = {**options,'target':options.get('draggable')}
    drop_opts:AbilityOpts = {**options,'target':options.get('droppable')}

    # 获取容器右侧坐标
    drag_coord = self.get_coord(drag_opts)
    drop_coord = self.get_coord(drop_opts)
    if not drag_coord or not drop_coord:
      return False
    
    loc:tuple[int,int] = self._get_border_position(drag_coord,drop_coord,options.get('direction'))
    self.drag_to_location({**drag_opts,'value':loc})
    return True

  def drag_to_right(self,options:AbilityOpts)->bool:
    return self.drag_to_border({'direction':'right',**options})

  def drag_to_left(self,options:AbilityOpts)->bool:
    return self.drag_to_border({'direction':'left',**options})

  def drag_to_top(self,options:AbilityOpts)->bool:  
    return self.drag_to_border({'direction':'top',**options})  

  def drag_to_bottom(self,options:AbilityOpts)->bool:
    return self.drag_to_border({'direction':'bottom',**options})

  def _get_border_position(self,drag_coord:dict[str,int],drop_coord:dict[str,int],direction:str)->tuple[int,int]:
    '''
    move_to calculate the postion to the element's center point, not its top left border
    '''
    x = drag_coord['left'] # init x-axis position
    y = drag_coord['top'] # init y-axis position
    half_width = round(drag_coord['width']/2)
    half_height = round(drag_coord['height']/2)

    if direction == 'left':
      x = drop_coord[direction]+half_width
    elif direction == 'right':
      x = drop_coord[direction]-half_width
    elif direction == 'top':
      y = drop_coord[direction]+half_height
    elif direction == 'bottom':
      y = drop_coord[direction]-half_height

    return (x,y)

  def get_coord(self,options:AbilityOpts)->dict[str,int]|None:
    '''
    Get the element's size and position
    Args:
      options (AbilityOpts): The element query options
    Returns:
      dict[str,int]|None: The element's size and position, or None if the element is not found
    '''
    coordinate = {}
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return None

    coordinate['left'] = round(elem.location.get('x'))
    coordinate['top'] = round(elem.location.get('y'))
    coordinate['width'] = round(elem.size.get('width'))
    coordinate['height'] = round(elem.size.get('height'))
    coordinate['right'] = coordinate['left']+coordinate['width']
    coordinate['bottom'] = coordinate['top']+coordinate['height']
    return coordinate

  def _get_draggable_and_droppable(self,options:AbilityOpts)->tuple[WebElement|None,WebElement|None]:
    darg_opts:AbilityOpts = {**options,'target':options.get('draggable')}
    drop_opts:AbilityOpts = {**options,'target':options.get('droppable')}
    draggable = self._querier.query_element(darg_opts)
    droppable = self._querier.query_element(drop_opts)
    if not droppable or not draggable:
      return None,None
    return draggable,droppable


