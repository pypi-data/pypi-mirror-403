from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.dp.facade.DynamicFacade import DynamicFacade
from blues_lib.ability.atom.webdriver.DriverAbilityDict import DriverAbilityDict
from blues_lib.ability.atom.BaseAbility import BaseAbility

class DriverAbilityFacade(DynamicFacade):
    
  def __init__(self,driver:WebDriver) -> None:
    self._driver = driver
    super().__init__()
    
  def _get_class_instances(self) -> dict[str,BaseAbility]:
    return DriverAbilityDict.get(self._driver) if self._driver else {}
