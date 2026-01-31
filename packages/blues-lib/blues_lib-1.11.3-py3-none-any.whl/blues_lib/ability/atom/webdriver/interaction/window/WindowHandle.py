from blues_lib.ability.atom.webdriver.interaction.window.WindowBase import WindowBase

class WindowHandle(WindowBase):

  def get_current_window_handle(self)->str:
    '''
    Get the current window id
    Returns:
      str ： handle id, like: '3D31BF6D96E5671253E70BCF33DC7F39'
    '''
    return self._driver.current_window_handle

  def get_window_handles(self)->list[str]:
    '''
    Get all window's handles
    Returns:
      list[str] ： handles list, like: ['3D31BF6D96E5671253E70BCF33DC7F39']
    '''
    return self._driver.window_handles

  def get_latest_window_handle(self)->str:
    '''
    Get the latest opened window handle
    Returns:
      str ： handle id, like: '3D31BF6D96E5671253E70BCF33DC7F39'
    '''
    return self.get_window_handles()[-1]


