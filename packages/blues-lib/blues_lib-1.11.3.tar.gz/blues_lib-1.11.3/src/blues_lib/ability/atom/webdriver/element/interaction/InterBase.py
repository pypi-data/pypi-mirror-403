from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.ability.atom.webdriver.interaction.JavaScript import JavaScript
from blues_lib.ability.atom.webdriver.action.Keyboard import Keyboard

class InterBase(DriverAbility):
  """
  Interaction class to interact with element.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/interactions/
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)
    self._javascript = JavaScript(driver)
    self._keyboard = Keyboard(driver)
