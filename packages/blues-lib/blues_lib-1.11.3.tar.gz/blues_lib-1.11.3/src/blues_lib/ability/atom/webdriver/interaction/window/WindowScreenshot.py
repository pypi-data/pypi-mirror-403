import os
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.interaction.window.WindowBase import WindowBase
from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.dp.file.File import File   
from blues_lib.types.common import AbilityOpts,ElementTarget

class WindowScreenshot(WindowBase):

  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)

  def save_screenshot(self,options:AbilityOpts|None=None)->str:
    '''
    Take screenshot and save as image
    Args:
      options (AbilityOpts) : the options
        - value (str) : the screenshot value
    Returns:
      str : the download file path
    '''
    default_path = self._get_default_path()
    options = options or {}
    value:str = options.get('value','')
    target:ElementTarget = options.get('target','')
    shot_path:str = value or default_path
    
    if target:
      elem:WebElement|None = self._querier.query_element(options)
    else:
      elem = None

    if elem:
      stat = elem.screenshot(shot_path)
    else:
      stat = self._driver.save_screenshot(shot_path)
    return shot_path if stat else ''

  def _get_default_path(self,prefix='screenshot'):
    file_dir:str = File.get_dir_path('screenshot') # 已经包含尾部目录分割线
    file_name:str = File.get_file_name(prefix=prefix,extension='png')
    return os.path.join(file_dir,file_name)
