from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from blues_lib.types.common import AbilityOpts,ElementRoot
from blues_lib.ability.atom.webdriver.element.interaction.InterBase import InterBase
from blues_lib.ability.atom.webdriver.element.interaction.InterClick import InterClick

class InterChoice(InterBase):
  '''
  Choice the radio-like or choicebox-like's items
    - has no the input element
    - specific the click element
  Args:
    options (AbilityOpts): The element query options
  Returns:
    bool
  '''

  def __init__(self,driver:WebDriver):
    super().__init__(driver)
    self._click = InterClick(driver)
  
  def choice_by_text(self,options:AbilityOpts)->bool:
    return self._choice('text',options)
  
  def choice_by_no(self,options:AbilityOpts)->bool:
    return self._choice('no',options)
  
  def choice_by_index(self,options:AbilityOpts)->bool:
    return self._choice('index',options)
  
  def choice_all(self,options:AbilityOpts)->bool:
    return self._choice('all',options)

  def _choice(self,choice_by:str,options:AbilityOpts)->bool:
    '''
    Choice the radio-like or choicebox-like's items
    Args:
      value (list[str]|str) : the choice values
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    elems:list[WebElement]|None = self._get_choice_options(choice_by,options)
    if not elems:
      return False
    
    for elem in elems:
      self._click.click({'target':elem})
    return True

  def _get_choice_options(self,choice_by:str,options:AbilityOpts)->list[WebElement]|None:
    root:ElementRoot|None = options.get('root')
    target:str|None = options.get('target')
    if not root or not target:
      return None

    if not choice_by or choice_by == 'all':
      # must be a string selector
      target_selectors = target
    else:
      target_selectors:list[str] = []
      value = options.get('value')
      values:list[str] = value if isinstance(value,list) else [value]

      for val in values:
        if choice_by == 'text':
          selector:str = f'xpath:./descendant::{target}[contains(normalize-space(text()),"{val}")]'
        elif choice_by == 'index':
          position:int = int(val)+1
          selector:str = f'xpath:./descendant::{target}[{position}]'
        elif choice_by == 'no':
          selector:str = f'xpath:./descendant::{target}[{val}]'
        target_selectors.append(selector) 
    
    opts = {
      **options,
      'target':target_selectors,
      'root':root,
    }
    elems:list[WebElement]|None = self._querier.query_elements(opts)
    return elems if elems else None
