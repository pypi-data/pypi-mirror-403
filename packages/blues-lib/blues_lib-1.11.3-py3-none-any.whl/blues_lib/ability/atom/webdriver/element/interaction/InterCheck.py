from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from blues_lib.types.common import ElementTarget,AbilityOpts
from blues_lib.ability.atom.webdriver.element.interaction.InterBase import InterBase
from blues_lib.ability.atom.webdriver.element.interaction.InterClick import InterClick

class InterCheck(InterBase):

  def __init__(self,driver:WebDriver):
    super().__init__(driver)
    self._click = InterClick(driver)
  
  def check_by_value(self,options:AbilityOpts)->bool:
    return self._check('value',options)
  
  def check_by_no(self,options:AbilityOpts)->bool:
    return self._check('no',options)
  
  def check_by_index(self,options:AbilityOpts)->bool:
    '''
    Check the radio or checkbox's items by index
    Args:
      options (AbilityOpts): The element query options
    '''
    return self._check('index',options)
  
  def check_all(self,options:AbilityOpts)->bool:
    return self._check('all',options)

  def _check(self,check_by:str,options:AbilityOpts)->bool:
    '''
    Check the radio or checkbox's items
    Args:
      value (list[str]|str) : the check values
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    elems:list[WebElement]|None = self._get_check_options(check_by,options)
    if not elems:
      return False
    
    for elem in elems:
      if not elem.is_selected():
        self._click.click({'target':elem})
    return True
  
  def uncheck_by_value(self,options:AbilityOpts)->bool:
    return self._uncheck('value',options)

  def uncheck_by_no(self,options:AbilityOpts)->bool:
    return self._uncheck('no',options)
  
  def uncheck_by_index(self,options:AbilityOpts)->bool:
    '''
    Uncheck the radio or checkbox's items by index
    Args:
      options (AbilityOpts): The element query options
    '''
    return self._uncheck('index',options)
  
  def uncheck_all(self,options:AbilityOpts)->bool:
    return self._uncheck('all',options)

  def _uncheck(self,check_by:str,options:AbilityOpts)->bool:
    '''
    Uncheck the radio or checkbox's items by value or index
    Args:
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    elems:list[WebElement]|None = self._get_check_options(check_by,options)
    if not elems:
      return False

    for elem in elems:
      if elem.is_selected():
        self._click.click({'target':elem})
    return True

  
  def toggle_by_value(self,options:AbilityOpts)->bool:
    return self._toggle_check('value',options)
  
  
  def toggle_by_index(self,options:AbilityOpts)->bool:
    return self._toggle_check('index',options)

  
  def toggle_all(self,options:AbilityOpts)->bool:
    return self._toggle_check('all',options)

  def _toggle_check(self,check_by:str,options:AbilityOpts)->bool:
    '''
    Toggle the check state of the radio or checkbox's items
    Args:
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    elems:list[WebElement]|None = self._get_check_options(check_by,options)
    if not elems:
      return False

    for elem in elems:
      if elem.is_selected():
        self._click.click({'target':elem})
    return True

  def _get_check_options(self,check_by:str,options:AbilityOpts)->list[WebElement]|None:
    target:ElementTarget|None = options.get('target')
    if not target:
      return None

    if not check_by or check_by == 'all':
      # must be a string selector
      target_selectors = 'input[type=checkbox],input[type=radio]'
    else:
      target_selectors:list[str] = []
      value = options.get('value')
      values:list[str] = value if isinstance(value,list) else [value]

      for val in values:
        if check_by == 'value':
          selector:str = f'xpath:./descendant::input[@type="radio" or @type="checkbox"][@value="{val}"]'
        elif check_by == 'index':
          position:int = int(val)+1
          selector:str = f'xpath:./descendant::input[@type="radio" or @type="checkbox"][{position}]'
        elif check_by == 'no':
          selector:str = f'xpath:./descendant::input[@type="radio" or @type="checkbox"][{val}]'
        target_selectors.append(selector) 
    
    opts = {
      **options,
      'target':target_selectors,
      'root':target,
    }
    elems:list[WebElement]|None = self._querier.query_elements(opts)
    return elems if elems else None
