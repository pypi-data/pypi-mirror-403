from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class MouseBase(DriverAbility):
  """
  Working with mouse actions
  Reference : https://www.selenium.dev/documentation/webdriver/actions_api/mouse/
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)
    self._chains = ActionChains(driver)
    self._builder = ActionBuilder(driver)
