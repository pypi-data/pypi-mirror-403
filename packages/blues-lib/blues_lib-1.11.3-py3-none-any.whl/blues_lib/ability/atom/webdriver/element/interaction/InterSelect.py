from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.element.Information import Information  
from blues_lib.ability.atom.webdriver.element.interaction.InterBase import InterBase

class InterSelect(InterBase):
  '''
  That this class only works for HTML elements select and option. 
  It is possible to design drop-downs with JavaScript overlays using div or li, and this class will not work for those
  '''
 
  def _init_(self,driver):
    super()._init_(driver)
    self._info = Information(driver)

  
  def get_options(self,options:AbilityOpts)->list[dict]|None:
    '''
    Get the options of the select element.
    Args:
      options (AbilityOpts): The element query options
    Returns:
      list<dict>
    '''
    select:Select|None =self._get_select(options)
    if not select:
      return None

    return self._get_option_items(select.options)

  
  def get_selected_options(self,options:AbilityOpts)->list[dict]|None:
    '''
    Get the selected options of the select element.
    Args:
      options (AbilityOpts): The element query options
    Returns:
      list<dict>    
    '''
    select:Select|None =self._get_select(options)
    if not select:
      return None
    return self._get_option_items(select.all_selected_options)

  
  def get_first_selected_option(self,options:AbilityOpts)->dict|None:
    '''
    Get the first selected option of the select element.
    Args:
      options (AbilityOpts): The element query options
    Returns:
      dict|None
    '''
    select:Select|None =self._get_select(options)
    if not select:
      return None
    items:list[dict] = self._get_option_items([select.first_selected_option]) 
    return items[0] if items else None

  
  def select_by_index(self,options:AbilityOpts)->bool:
    '''
    Select a option by index
    Args:
      options (AbilityOpts): The element query options
        - value (int|list[int]): the option's index or indices, index start from 0
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False

    value = options.get('value')
    indexs = value if type(value)==list else [value]
    for idx in indexs:
      select.select_by_index(idx)
    return True
  
  
  def select_by_value(self,options:AbilityOpts)->bool:
    '''
    Select a option by value
    Args:
      options (AbilityOpts): The element query options
        - value (str|list[str]): the option's value or values
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    
    value = options.get('value')
    values = value if type(value)==list else [value]
    for val in values:
      select.select_by_value(val)
    return True
  
  
  def select_by_visible_text(self,options:AbilityOpts)->bool:
    '''
    Select a option by visible text
    Args:
      options (AbilityOpts): The element query options
        - value (str|list[str]): the option's visible text or texts
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    
    value = options.get('value')
    texts = value if type(value)==list else [value]
    for txt in texts:
      select.select_by_visible_text(txt)
    return True

  
  def deselect_all(self,options:AbilityOpts)->bool:
    '''
    You may only deselect all options of a multi-select
      - only for multiple select elements
    Args:
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False

    if not select.is_multiple:
      return False

    select.deselect_all()
    return True
    
  
  def deselect_by_index(self,options:AbilityOpts)->bool:
    '''
    Deselect a option by index
    Args:
      options (AbilityOpts): The element query options
        - value (int|list[int]): the option's index or indices, index start from 0
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    
    value = options.get('value')
    indexs = value if type(value)==list else [value]
    for idx in indexs:
      select.deselect_by_index(idx)
    return True
  
  
  def deselect_by_value(self,options:AbilityOpts)->bool:
    '''
    Deselect a option by value
    Args:
      options (AbilityOpts): The element query options
        - value (str|list[str]): the option's value or values
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    
    value = options.get('value')
    values = value if type(value)==list else [value]
    for val in values:
      select.deselect_by_value(val)
    return True

  
  def deselect_by_visible_text(self,options:AbilityOpts)->bool:        
    '''
    Deselect a option by visible text
    Args:
      options (AbilityOpts): The element query options
        - value (str|list[str]): the option's visible text or texts
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    
    value = options.get('value')
    texts = value if type(value)==list else [value]
    for txt in texts:
      select.deselect_by_visible_text(txt)
    return True
  
  
  def is_multiple(self,options:AbilityOpts)->bool:
    '''
    Returns whether the select element is multiple
    Args:
      options (AbilityOpts): The element query options
    Returns:
      bool
    '''
    select:Select|None = self._get_select(options)
    if not select:
      return False
    return select.is_multiple

  def _get_select(self,options:AbilityOpts)->Select|None:
    '''
    Return the Select instance
    Args:
      options (AbilityOpts): The element query options
    Returns:
      Select 
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return None

    # must use the orig select element
    self._javascript.display_and_scroll_into_view(options)

    return Select(elem)
  
  def _get_option_items(self,elements)->list[dict]|None:
    if not elements:
      return None

    items = []
    for option in elements:
      items.append({
        'value':option.get_attribute('value'),
        'label':option.text,
      })
    return items



