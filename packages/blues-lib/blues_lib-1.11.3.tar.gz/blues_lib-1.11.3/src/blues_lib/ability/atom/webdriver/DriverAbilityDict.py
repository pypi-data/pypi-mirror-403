from selenium.webdriver.remote.webdriver import WebDriver
# driver
from blues_lib.ability.atom.webdriver.driver.Session import Session

# element 
from blues_lib.ability.atom.webdriver.element.Finder import Finder
from blues_lib.ability.atom.webdriver.element.Information import Information 
from blues_lib.ability.atom.webdriver.element.Interaction import Interaction 
from blues_lib.ability.atom.webdriver.element.File import File

# action api
from blues_lib.ability.atom.webdriver.action.Keyboard import Keyboard
from blues_lib.ability.atom.webdriver.action.Mouse import Mouse
from blues_lib.ability.atom.webdriver.action.Wheel import Wheel

# interaction
from blues_lib.ability.atom.webdriver.interaction.JavaScript import JavaScript 
from blues_lib.ability.atom.webdriver.interaction.Navigation import Navigation
from blues_lib.ability.atom.webdriver.interaction.Window import Window
from blues_lib.ability.atom.webdriver.interaction.Cookie import Cookie
from blues_lib.ability.atom.webdriver.interaction.Alerts import Alerts
from blues_lib.ability.atom.webdriver.interaction.Frame import Frame
from blues_lib.ability.atom.webdriver.interaction.Browser import Browser

# wait
from blues_lib.ability.atom.webdriver.wait.EC import EC
from blues_lib.ability.atom.webdriver.wait.Querier import Querier

class DriverAbilityDict():

  @classmethod
  def get(cls,driver:WebDriver)->dict:
    return {
      # driver
      Session.__name__:Session(driver),
        
      # element 
      Finder.__name__:Finder(driver),
      Information.__name__:Information(driver),
      Interaction.__name__:Interaction(driver),
      File.__name__:File(driver),

      # action api
      Keyboard.__name__:Keyboard(driver),
      Mouse.__name__:Mouse(driver),
      Wheel.__name__:Wheel(driver),

      # interaction
      JavaScript.__name__:JavaScript(driver),
      Navigation.__name__:Navigation(driver),
      Window.__name__:Window(driver),
      Cookie.__name__:Cookie(driver),
      Alerts.__name__:Alerts(driver),
      Frame.__name__:Frame(driver),
      Browser.__name__:Browser(driver),
      
      # wait
      EC.__name__:EC(driver),
      Querier.__name__:Querier(driver),
    }