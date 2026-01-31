import logging
from typing import Callable
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.metastore.validate.MetaValidator import MetaValidator
from blues_lib.types.common import DriverDef,DriverMode,DriverStartupOpts,DriverLocOpts,LoginMode,LoginOpts,AbilityDef,SeqDef
from blues_lib.ability.atom.webdriver.driver.DriverFactory import DriverFactory   
from blues_lib.metastore.template.MetaTemplate import MetaTemplate
from blues_lib.ability.AbilityExecutor import AbilityExecutor

class DriverInitializer:
  def __init__(self,driver_def:DriverDef,bizdata:dict|None=None) -> None:
    self._driver_def = driver_def
    self._bizdata = bizdata
    self._logger = logging.getLogger('airflow.task')

  def init(self)->WebDriver:
    validate_tpl = 'except.input.driver_def'
    MetaValidator.validate_with_template(self._driver_def,validate_tpl)

    mode:DriverMode = self._driver_def.get('mode') or 'cft'
    startup_opts:DriverStartupOpts = self._driver_def.get('startup') or {}
    location_opts:DriverLocOpts = self._driver_def.get('location') or {}

    factory =  DriverFactory(**startup_opts)
    method:Callable = getattr(factory,mode)
    self._logger.info(f"{self.__class__.__name__} driver mode ⌜{mode}⌟ {location_opts}")
    driver:WebDriver = method(**location_opts)
    self._login(driver)
    return driver
  
  def _login(self,driver:WebDriver)->None:
    login_opts:LoginOpts = self._driver_def.get('login') or {}
    login_mode:LoginMode = login_opts.get('mode')
    ephemeral:bool = login_opts.get('ephemeral',False)
    
    if not login_mode:
      return

    login_def:dict[str,AbilityDef|SeqDef] = {}
    if ephemeral:
      login_def = MetaTemplate.login_ephemeral(login_mode)
    else:
      login_def = MetaTemplate.login(login_mode)

    if not login_def:
      raise ValueError(f"login template of mode {login_mode} not found")

    try:
      AbilityExecutor(driver).execute(login_def,self._bizdata)
    except Exception as e:
      driver.quit()
      raise
