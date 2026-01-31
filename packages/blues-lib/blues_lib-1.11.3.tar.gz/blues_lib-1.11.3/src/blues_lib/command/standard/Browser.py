from blues_lib.command.NodeCommand import NodeCommand
from blues_lib.namespace.CommandName import CommandName
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.sele.browser.chrome.ChromeFactory import ChromeFactory   

class Browser(NodeCommand):
  
  NAME = CommandName.Standard.BROWSER

  def _invoke(self)->STDOut:
    browser = self._get_browser()
    self._context['browser'] = browser
    return STDOut(200,'browser created')

  def _get_browser(self):
    config:dict = self._config
    browser_conf:dict = config.get('browser') or {}
    driver_config =  browser_conf.get('config') or {} # optional
    driver_options = browser_conf.get('options') or {} # optional
    browser = ChromeFactory(**driver_options).create(driver_config)
    if not browser:
      raise Exception(f'[{self.NAME}] fail to create the browser')
    return browser