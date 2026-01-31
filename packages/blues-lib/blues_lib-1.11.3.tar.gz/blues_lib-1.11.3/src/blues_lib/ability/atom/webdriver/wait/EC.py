from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException 
from selenium.common.exceptions import ElementNotInteractableException 
from blues_lib.ability.atom.webdriver.wait.ec.ECInfo import  ECInfo
from blues_lib.ability.atom.webdriver.wait.ec.ECSwitch import ECSwitch
from blues_lib.ability.atom.webdriver.wait.ec.ECElementLocated import ECElementLocated
from blues_lib.ability.atom.webdriver.wait.ec.ECElementToBe import ECElementToBe
from blues_lib.types.common import AbilityOpts

class EC(ECInfo,ECSwitch,ECElementLocated,ECElementToBe):
  """
  official expected_conditions
  Reference: https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/
  """

  def until(self,options:AbilityOpts):
    options = self._get_ability_options(options)
    callback:callable = options.get('callback')
    timeout:int|float = options.get('timeout')
    message:str = options.get('message','until failed')
    poll_frequency:int|float = options.get('poll_frequency',0.5)
    ignored_exceptions:list = options.get('ignored_exceptions',[NoSuchElementException,ElementNotInteractableException])
    
    # can return any type result
    driver_wait = WebDriverWait(self._driver,timeout,poll_frequency,ignored_exceptions)
    return driver_wait.until(callback,message)
