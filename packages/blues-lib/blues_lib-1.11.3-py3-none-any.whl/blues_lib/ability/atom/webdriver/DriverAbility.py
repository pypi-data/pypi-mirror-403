from selenium.common.exceptions import NoSuchShadowRootException
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.BaseAbility import BaseAbility

class DriverAbility(BaseAbility):

  def __init__(self,driver):
    super().__init__()
    self._driver = driver
    self._default_options:AbilityOpts = {
      # locator
      'target':'',
      'root':driver,
      'draggable':'',
      'droppable':'',

      # limit
      'timeout':5,
      'interval':0,
      'duration':-1,
      'repeat':1,
    }

  def _is_shadow_host(self,element:WebElement)->bool:
    '''
    Check if the element is a shadow host.
      - every WebElement has a shadow_root attribute
      - if it's unavailable, access the attribute will raise NoSuchShadowRootException
    Args:
      element (WebElement): the element to check
    Returns:
      bool: True if the element has a shadow root, False otherwise
    '''
    try:
      shadow_root = element.shadow_root
      return shadow_root is not None
    except NoSuchShadowRootException:
      return False
    except AttributeError:
      return False

  def _get_ability_options(self,options:AbilityOpts|None)->AbilityOpts:
    if not options:
      return self._default_options
    return {**self._default_options,**options}
