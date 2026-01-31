from typing import Any
import json
import pyperclip
import time
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.element.interaction.InterBase import InterBase
from blues_lib.util.FileWriter import FileWriter

class InterClick(InterBase):

  
  def click(self,options:AbilityOpts)->bool:
    '''
    Click and release
    Args:
      options (AbilityOpts, optional): The options for clicking the element. Defaults to None.
    Returns:
      bool
    '''
    elem:WebElement|None = self._querier.query_element(options)     
    if not elem:
      return False
    
    # can't deal the elemen's parent's invisible
    self._javascript.display_and_scroll_into_view({**options,'target':elem})
    elem.click()
    return True

  
  def click_and_copy(self,options:AbilityOpts)->str:
    '''
    Click a button and copy the text to the clipboard
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      str : the copied content
    '''
    text:str = self._get_text(options)
    if not text:
      return ''

    if save_path:= options.get('save_path',''):
      return FileWriter.write_text(save_path,text)
    else:
      return text
  
  def click_and_copy_json(self,options:AbilityOpts)->Any:
    '''
    Click a button and copy the JSON text to the clipboard
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      Any : the parsed JSON object or empty string if parsing fails
    '''
    text:str = self._get_text(options)
    if not text:
      return ''

    try:
      content = json.loads(text)
      if save_path:= options.get('save_path',''):
        return FileWriter.write_json(save_path,content)
      else:
        return content
    except json.JSONDecodeError:
      self._logger.error(f"Failed to parse JSON from clipboard text: {text}")
      return ''
    
  def _get_text(self,options:AbilityOpts)->str:
    success:bool = self.click(options)
    if not success:
      return ''

    time.sleep(0.2)
    # get the text from the clipboard
    return pyperclip.paste()
