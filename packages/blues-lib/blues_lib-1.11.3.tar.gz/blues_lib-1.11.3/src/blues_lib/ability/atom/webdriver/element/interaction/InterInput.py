import time
import random
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.element.interaction.InterBase import InterBase

class InterInput(InterBase):
  """
  A high-level instruction set for manipulating form controls.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/interactions/

  It attempts to perform two things before attempting the specified action.
  1. If it determines the element is outside the viewport, it scrolls the element into view, specifically it will align the bottom of the element with the bottom of the viewport.
  2. It ensures the element is interactable before taking the action. 
  """
  
  def send_keys_and_enter(self,options:AbilityOpts)->bool:
    self.send_keys(options)
    time.sleep(0.5)
    self._keyboard.enter(options)
    return True
  
  def reset_chars(self,options:AbilityOpts)->bool:
    self._keyboard.clear(options)
    return self.send_chars(options)
  
  def send_chars(self,options:AbilityOpts)->bool:
    '''
    Reset the text in a editable element by character.
      - refind the element before input a char
    Args:
      options (AbilityOpts): The element query options
        - value (list[str]|str): The text to reset.
    Returns:
      bool
    '''
    value:list[str]|str|None = options.get('value')
    if not value:
      return False

    text:str = ''.join(value) if isinstance(value,list) else value
    # must wait for element refresh
    interval:int|float = self._get_interval(options.get('interval') or 0.5)

    self._javascript.display_and_scroll_into_view(options)
    self._keyboard.end(options)

    for idx,char in enumerate(text):
      if interval>0 and idx>0:
        time.sleep(interval)
      self.send_keys({**options,'value':char})
    return True
  
  def send_paras(self,options:AbilityOpts)->bool:
    '''
    Append text into a editable element by paragraph.
    '''
    para_options:dict = {'segment_lf':1}
    options['value'] = self._get_para_texts(options)
    opts:dict = {**para_options,**options}
    return self.send_keys(opts)
  
  def newline_and_send_paras(self,options:AbilityOpts)->bool:
    '''
    Add a new line then append text into a editable element by paragraph.
    '''
    para_options:dict = {'prefix_lf':1,'segment_lf':1}
    options['value'] = self._get_para_texts(options)
    opts:dict = {**para_options,**options}
    return self.send_keys(opts)

  def clear_and_send_paras(self,options:AbilityOpts)->bool:
    '''
    Clear the text in a editable element then append text into it by paragraph.
    '''
    para_options:dict = {'segment_lf':1,'clear':True}
    options['value'] = self._get_para_texts(options)
    opts:dict = {**para_options,**options}
    return self.send_keys(opts)
  
  def _get_para_texts(self,options:AbilityOpts)->list[str]:
    value:list[str]|str = options.get('value') or ''
    if isinstance(value,str):
      return [line.strip() for line in value.splitlines() if line.strip()]
    return value
  
  def clear_and_send_keys(self,options:AbilityOpts)->bool:
    clear_options:dict = {'clear':True}
    opts:dict = {**options,**clear_options}
    return self.send_keys(opts)

  def send_keys(self,options:AbilityOpts)->bool:
    '''
    Input text into a editable element.
    Args:
      options (AbilityOpts): The element query options
        - value (list[str]|str): The text to input.
    Returns:
      bool
    '''
    elem:WebElement|None = self._querier.query_element(options)
    value:list[str]|str|None = options.get('value') or ''
    if not elem:
      return False

    self._javascript.display_and_scroll_into_view(options)

    interval:int|float = self._get_interval(options.get('interval'))
    clear:bool = options.get('clear',False)
    # three kind of line feed count
    prefix_lf:int = options.get('prefix_lf',0)
    segment_lf:int = options.get('segment_lf',0)
    suffix_lf:int = options.get('suffix_lf',0)

    if clear:
      self._keyboard.clear(options)
    else:
      # make sure the cursor is at the end of the text
      self._keyboard.end(options)

    texts:list[str] = value if isinstance(value,list) else [value]
    texts = ['' if text is None else str(text) for text in texts]
    if prefix_lf>0:
      texts[0] = '\n'*prefix_lf + texts[0]
    if suffix_lf>0:
      texts[-1] += '\n'*suffix_lf

    lf_chars:str = '\n'*segment_lf if segment_lf>0 else ''
    if interval>0:
      for idx,text in enumerate(texts):
        if idx>0:
          time.sleep(interval)
          elem.send_keys(lf_chars,text)
        else:
          elem.send_keys(text)
    else:
      elem.send_keys(lf_chars.join(texts))
    return True

  def _get_interval(self,interval:int|float|list[int|float])->int|float:
    value = interval or 0
    if isinstance(interval,list):
      min_val,max_val = interval
      min_int = int(min_val * 2)
      max_int = int(max_val * 2)
      random_int = random.randint(min_int, max_int)
      # 缩小2倍，得到“整数/x.5小数”
      value = random_int * 0.5
    return value if value>=0 else 0
