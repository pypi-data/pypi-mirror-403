from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.ability.atom.matcher.MatcherAbilityDict import MatcherAbilityDict
from blues_lib.dp.facade.DynamicFacade import DynamicFacade

class MatcherAbilityProxy(DynamicFacade):

  def __init__(self,driver:WebDriver) -> None:
    self._class_instances = MatcherAbilityDict.get(driver)
    super().__init__()