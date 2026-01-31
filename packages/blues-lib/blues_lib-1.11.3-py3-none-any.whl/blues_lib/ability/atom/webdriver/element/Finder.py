from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.LocatorCreator import LocatorCreator
from blues_lib.types.common import AbilityOpts,ElementRoot,SearchContext
from blues_lib.deco.ability.ExceptionLog import ExceptionLog
from blues_lib.ability.atom.webdriver.DriverSearcher import DriverSearcher

class Finder(DriverSearcher):
  """
  Finder class to find elements using different strategies.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/finders/
  """

  def find_element(self,options:AbilityOpts)->WebElement|None:
    return self._search_element(options)

  def find_elements(self,options:AbilityOpts)->list[WebElement]|None:
    return self._search_elements(options)

  @ExceptionLog()
  def _get_element(self,options:AbilityOpts)->WebElement|None:
    """
    Find the first element using the base webdriver method
    Parameter:
      options (AbilityOpts): the options for querying the element
    Returns:
      WebElement|None : the first element that matches the target or None if not found
    """
    target:str = options.get('target')
    locator = LocatorCreator.create(target)

    root:ElementRoot = options.get('root')
    context:SearchContext = self._get_context(root)
    return context.find_element(*locator)
  
  @ExceptionLog()
  def _get_elements(self,options:AbilityOpts)->list[WebElement]|None:
    """
    Find all elements using the base webdriver method
    Parameter:
      options (AbilityOpts): the options for querying the elements
    Returns:
      list[WebElement]|None : the list of elements that matches the target or None if not found
    """
    target:str = options.get('target')
    locator = LocatorCreator.create(target)

    root:ElementRoot = options.get('root')
    context:SearchContext = self._get_context(root)
    return context.find_elements(*locator) or None

  def _get_context(self,root:ElementRoot)->SearchContext:
    '''
    Find and return the element root, contains 3 kinds of root:
    1. WebElement: return the element
    2. WebDriver: return the driver 
    3. ShadowRoot: return the shadow root 
    '''
    if not root:
      return self._driver
    if isinstance(root,SearchContext):
      return root
    elem:WebElement|None = self._get_root_element(root)
    if not elem:
      return self._driver
    return elem.shadow_root if self._is_shadow_host(elem) else elem

  def _get_root_element(self,root:str)->WebElement|None:
    locator = LocatorCreator.create(root)
    try:
      return self._driver.find_element(*locator)
    except:
      return None

