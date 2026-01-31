from blues_lib.ability.atom.webdriver.interaction.window.WindowBase import WindowBase
from blues_lib.util.BluesType import BluesType 
from blues_lib.types.common import AbilityOpts

class WindowSwitch(WindowBase):
 
  def switch_to_new_window(self,options:AbilityOpts|None=None)->bool:
    """
    Open a new window and switch to it automatically
    Args:
      options (AbilityOpts) : the options for opening the new window
    Returns:
      bool : True if switch to the new window successfully, False otherwise
    """
    self._driver.switch_to.new_window('window')
    value:str = options.get('value','') if options else ''
    if value:
      self._driver.get(value)
    return True
      
  def switch_to_new_tab(self,options:AbilityOpts|None=None)->bool:
    """
    Open a new tab  and switch to it automatically
    Args:
      options (AbilityOpts) : the options for opening the new tab
    Returns:
      bool : True if switch to the new tab successfully, False otherwise
    """
    self._driver.switch_to.new_window('tab')
    value:str = options.get('value','') if options else ''
    if value:
      self._driver.get(value)
    return True
      
  def switch_to_window(self,options:AbilityOpts|None=None)->bool:
    """
    Switch to the specified window
    Args:
      options (AbilityOpts) : the options for switching to the window
    Returns:
      bool : True if switch to the window successfully, False otherwise
    """
    value:str = options.get('value','') if options else ''
    if not value:
      return False

    if self._driver.current_window_handle == value:
      return True

    self._driver.switch_to.window(value)
    return True

  def switch_to_latest_window(self)->bool:
    """
    Switch to the latest opened window
    Returns:
      bool : True if switch to the latest window successfully, False otherwise
    """
    handles:list[str] = self._driver.window_handles
    self._driver.switch_to.window(handles[-1])
    return True

  def close_and_switch_to_first_content(self)->bool:
    '''
    Close the current window and switch to the first window
    Returns:
      bool : True if switch to the first window successfully, False otherwise
    '''
    self._driver.close()
    return self.switch_to_first_content()
     
  def switch_to_first_content(self)->bool:
    '''
    Switch to the first window
    Returns:
      bool : True if switch to the first window successfully, False otherwise
    '''
    handles:list[str] = self._driver.window_handles
    if handles:
      self._driver.switch_to.window(handles[0])
      return True
    else:
      return False

  def close_and_switch_to_prev_content(self)->bool:
    '''
    Close the current window and switch to the prev window or tab
    Returns:
      bool : True if switch to the prev window successfully, False otherwise
    '''
    return self.switch_to_prev_content(True)
      
  def switch_to_prev_content(self,close_before_switch:bool=False)->bool:
    '''
    Switch to the prev window or tab
    Returns:
      bool : True if switch to the prev window successfully, False otherwise
    '''
    current_handle = self._driver.current_window_handle
    handles:list[str] = self._driver.window_handles
    current_handle_index = BluesType.last_index(handles,current_handle)
    if current_handle_index>0:
      prev_handle = handles[current_handle_index-1]
      if close_before_switch:
        self._driver.close()
      self._driver.switch_to.window(prev_handle)
    return True

  def close_and_switch_to_next_content(self)->bool:
    '''
    Close the current window and switch to the next window or tab
    Returns:
      bool : True if switch to the next window successfully, False otherwise
    '''
    return self.switch_to_next_content(True)

  def switch_to_next_content(self,close_before_switch:bool=False)->bool:
    '''
    Switch to the next window or tab
    Returns:
      bool : True if switch to the next window successfully, False otherwise
    '''
    current_handle = self._driver.current_window_handle
    handles:list[str] = self._driver.window_handles
    current_handle_index = BluesType.last_index(handles,current_handle)
    if current_handle_index<len(handles)-1:
      next_handle = handles[current_handle_index+1]
      if close_before_switch:
        self._driver.close()
      self._driver.switch_to.window(next_handle)
    return True
