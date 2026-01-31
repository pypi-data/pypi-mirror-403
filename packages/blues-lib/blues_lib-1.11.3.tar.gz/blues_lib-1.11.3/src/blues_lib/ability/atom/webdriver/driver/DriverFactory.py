from pathlib import Path
from selenium import webdriver
import undetected_chromedriver
from blues_lib.ability.atom.webdriver.driver.options.OptionsGetter import OptionsGetter
from blues_lib.ability.atom.webdriver.driver.service.ServiceGetter import ServiceGetter
from blues_lib.ability.atom.webdriver.driver.cdp.CDPSetter import CDPSetter
from blues_lib.sele.browser.driver.CFTInstaller import CFTInstaller
from blues_lib.ability.atom.webdriver.driver.options.OptionsFeature import OptionsFeature

class DriverFactory:

  def __init__(self,features:list[str]|None=None,caps:dict|None=None,arguments:list|None=None,exp_options:dict|None=None,extensions:list|None=None,cdp_cmds:dict|None=None):
    self._options_kwargs = {
      'caps':caps or {},
      'arguments':arguments or [],
      'exp_options':exp_options or {},
      'extensions':extensions or [],
    }
    self._cdp_cmds = cdp_cmds or {}
    if features:
      OptionsFeature(self._options_kwargs,self._cdp_cmds).set(features)

  def remote(self,command_executor:str)->webdriver.Remote:
    # remote for chrome
    options = OptionsGetter(**self._options_kwargs).chrome()
    driver = webdriver.Remote( command_executor = command_executor, options = options)
    CDPSetter(driver,self._cdp_cmds).set()
    return driver

  def cft(self)->webdriver.Chrome:
    # chrome for testing
    executable_path, binary_location = self._install_cft()
    return self.chrome(executable_path,binary_location)

  def udcft(self)->undetected_chromedriver.Chrome:
    # chrome for testing
    executable_path, binary_location = self._install_cft()
    return self.udc(executable_path,binary_location)

  def udc(self,executable_path:str='',binary_location:str='')->undetected_chromedriver.Chrome:
    # udc use it's own arguments / exp_options / cdp_cmds
    caps:dict = self._options_kwargs['caps']
    if binary_location:
      caps['binary_location'] = binary_location
    options = OptionsGetter(**self._options_kwargs).udc()
    return undetected_chromedriver.Chrome( driver_executable_path = executable_path, options = options)

  def chrome(self,executable_path:str='',binary_location:str='')->webdriver.Chrome:
    '''
    Create a Chrome driver
    Args:
      executable_path (str): The path to the ChromeDriver executable. if it's empty, will find it in PATH.
      binary_location (str): The path to the Chrome binary. if it's empty, will find it in PATH.
    Returns:
      webdriver.Chrome: The Chrome driver instance.
    '''
    if executable_path:
      service = ServiceGetter.chrome(executable_path=executable_path)
    else:
      service = ServiceGetter.chrome()

    if binary_location:
      self._options_kwargs['caps']['binary_location'] = binary_location

    options = OptionsGetter(**self._options_kwargs).chrome()
    driver = webdriver.Chrome( service = service, options = options)

    CDPSetter(driver,self._cdp_cmds).set()
    return driver

  def _install_cft(self)->tuple[str,str]:
    result:dict = CFTInstaller.install()
    if result.get('error'):
      raise Exception(f"Failed to install CFT ChromeDriver: {result.get('error')}")

    # CFT chrome和driver必须匹配使用
    executable_path = Path(result.get('driver_path')).as_posix()
    binary_location = Path(result.get('chrome_path')).as_posix()
    return executable_path, binary_location