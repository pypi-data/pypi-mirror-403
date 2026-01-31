from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from blues_lib.ability.atom.webdriver.element.Information import Information  
from blues_lib.ability.atom.webdriver.interaction.JavaScript import JavaScript
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class FileBase(DriverAbility):
  """
  File class to get element information.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/information/
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver) 
    self._info = Information(driver)
    self._javascript = JavaScript(driver)

