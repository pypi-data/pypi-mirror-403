from blues_lib.ability.atom.webdriver.interaction.window.WindowBase import WindowBase
from blues_lib.types.common import AbilityOpts

class WindowRect(WindowBase):

  def maximize_window(self)->bool:
    '''
    Maximize the window
    Returns:
      bool : True if maximize the window successfully, False otherwise
    '''
    self._driver.maximize_window()
    return True

  def minimize_window(self)->bool:
    '''
    Minimize the window
    Returns:
      bool : True if minimize the window successfully, False otherwise
    '''
    self._driver.minimize_window()
    return True

  def fullscreen_window(self)->bool:
    '''
    Maximize and hide the top tool bar
    Returns:
      bool : True if fullscreen the window successfully, False otherwise
    '''
    self._driver.fullscreen_window()
    return True

  def get_window_size(self)->dict[str,int]:
    '''
    Get the window size
    Returns:
      dict[str,int] : the size dict, like: {'width': 1755, 'height': 946}
    '''
    return self._driver.get_window_size()
  
  
  def set_window_size(self,options:AbilityOpts)->bool:
    '''
    Set the window size
    Args:
      options (AbilityOpts) : the options
        - value (list[int]) : window's size, like: [1000,500]
    Returns:
      bool : True if set the window size successfully, False otherwise
    '''
    size:list[int] = options.get('value',[])
    if not isinstance(size,list) or len(size) != 2:
      return False

    self._driver.set_window_size(*size)
    return True

  def get_window_position(self)->dict[str,int]:
    '''
    Get the window's position
    Returns:
      dict[str,int] : the position dict,like:  {'x': 99, 'y': 49}
    '''
    return self._driver.get_window_position()
     
  
  def set_window_position(self,options:AbilityOpts)->bool:
    '''
    Set the window's position
    Args:
      options (AbilityOpts) : the options
        - value (list[int]) : the position, like: [99,49]
    Returns:
      bool : True if set the window position successfully, False otherwise
    '''
    position:list[int] = options.get('value',[])
    if not isinstance(position,list) or len(position) != 2:
      return False

    self._driver.set_window_position(*position)
    return True