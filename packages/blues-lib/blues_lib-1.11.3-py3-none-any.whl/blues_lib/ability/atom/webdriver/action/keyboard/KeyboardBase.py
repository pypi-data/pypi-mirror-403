from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from selenium.webdriver import ActionChains
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.action.keyboard.OSKeys import OSKeys
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class KeyboardBase(DriverAbility):
  """
  Working with keyboard actions
  Reference : https://www.selenium.dev/documentation/webdriver/actions_api/keyboard/
  """
  
  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)

  def hold_ctrl_and_press(self,options:AbilityOpts)->bool:
    """
    Hold the ctrl key and press the keys
    Args:
      options (AbilityOpts): The element query options
    """
    value:list[str]|str = options.get('value')
    texts:list[str] = value if isinstance(value,list) else [value]
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False

    # always as a local variable, don't need to reset_actions
    chains = ActionChains(self._driver)
    ctrl:str = OSKeys.get('ctrl')

    chains.key_down(ctrl)
    self._press_keys(chains,texts,elem)
    chains.key_up(ctrl)

    chains.perform()
    chains.reset_actions()
    return True

  def press(self,options:AbilityOpts)->bool:
    """
    Press the keys
    Args:
      options (AbilityOpts): The element query options
    """
    value:list[str]|str = options.get('value')
    repeat:int = options.get('repeat') or 1
    interval:int = options.get('interval') or 0

    elem:WebElement|None = self._querier.query_element(options)

    chains = ActionChains(self._driver)
    texts:list[str] = value if isinstance(value,list) else [value]
    texts = texts * repeat

    if interval>0:
      for idx,text in enumerate(texts):
        self._press_keys(chains,[text],elem)
        if idx < len(texts)-1:
          chains.pause(interval)
    else:
      self._press_keys(chains,texts,elem)

    chains.perform()
    chains.reset_actions()
    return True

  def _press_keys(self,chains:ActionChains,texts:list[str],elem:WebElement|None=None)->bool:
    chains.send_keys_to_element(elem,*texts) if elem else chains.send_keys(*texts)
    return True
