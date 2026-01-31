from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.ability.sequence.SeqAbilityDict import SeqAbilityDict
from blues_lib.dp.facade.DynamicFacade import DynamicFacade

class SeqAbilityProxy(DynamicFacade):

  def __init__(self,driver:WebDriver) -> None:
    self._class_instances = SeqAbilityDict.get(driver)
    super().__init__()