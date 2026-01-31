from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.types.common import AbilityOpts

class Frame(DriverAbility):

  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)
 
  def switch_to_frame(self,options:AbilityOpts)->bool:
    '''
    Switch the driver's focus to the specific frame
    Parameter:
      options (AbilityOpts) : the frame's css selector or webelement
    Returns:
      bool : True if switch to the frame successfully, False otherwise
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem or not self._is_frame_tag(elem):
      return False

    self._driver.switch_to.frame(elem)
    return True

  def _is_frame_tag(self,elem:WebElement)->bool:
    tab_name:str = elem.tag_name.lower()
    return tab_name == 'iframe' or tab_name == 'frame'
      
  def switch_to_default_content(self)->bool:
    '''
    Switch to the default window that the driver opened
      - only work for from the frame to the main window
      - can't be used to switch between windows or tabs
    Returns:
      bool : True if switch to the default window successfully, False otherwise
    '''
    self._driver.switch_to.default_content() # always return None
    return True

  def switch_to_parent_frame(self)->bool:
    '''
    Switch to the current frame's parent window
    Returns:
      bool : True if switch to the parent window successfully, False otherwise
    '''
    self._driver.switch_to.parent_frame() # always return None
    return True
