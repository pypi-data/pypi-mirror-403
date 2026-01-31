from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class InfoBase(DriverAbility):
  """
  Information class to get element information.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/information/
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)
