import pyperclip
from selenium.webdriver.common.keys import Keys
from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardBase import KeyboardBase
from blues_lib.types.common import AbilityOpts

class KeyboardHotkey(KeyboardBase):

  def home(self,options:AbilityOpts)->bool:
    """
    Move the cursor to the home of the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = Keys.HOME
    return self.hold_ctrl_and_press(options)

  def end(self,options:AbilityOpts)->bool:
    """
    Move the cursor to the end of the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = Keys.END
    return self.hold_ctrl_and_press(options)

  def end(self,options:AbilityOpts)->bool:
    """
    Move the cursor to the end of the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = Keys.END
    return self.hold_ctrl_and_press(options)

  def select(self,options:AbilityOpts)->bool:
    """
    Select all the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = 'a'
    return self.hold_ctrl_and_press(options)

  def copy(self,options:AbilityOpts)->bool:
    """
    Select all text then copy the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = 'ac'
    return self.hold_ctrl_and_press(options)

  def cut(self,options:AbilityOpts)->bool:
    """
    Select all text then cut the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = 'ax'
    return self.hold_ctrl_and_press(options)

  def paste(self,options:AbilityOpts)->bool:
    """
    Move the cursor to the end of the text then paste the text in the input or contenteditable element
    Args:
      value (list[str]|str|None): The value to paste, if is empty copy from the clipboard
      options (AbilityOpts): The element query options
    """
    value:list[str]|str|None = options.get('value')
    if value:
      lines:str = self._get_lines(value,options)
      pyperclip.copy(lines) # write to clipboard

    options['value'] = [Keys.END,"v"]
    return self.hold_ctrl_and_press(options)

  def clear(self,options:AbilityOpts)->bool:
    """
    Select all text then delete the text in the input or contenteditable element
    Args:
      options (AbilityOpts): The element query options
    """
    options['value'] = ["a",Keys.DELETE]
    return self.hold_ctrl_and_press(options)

  def clear_and_paste(self,options:AbilityOpts)->bool:
    """
    Select all text then paste the text in the input or contenteditable element
    Args:
      value (list[str]|str|None): The value to paste, if is empty copy from the clipboard
      options (AbilityOpts): The element query options
    """
    value:list[str]|str|None = options.get('value')
    if value:
      lines:str = self._get_lines(value,options)
      pyperclip.copy(lines) # write to clipboard

    options['value'] = "av"
    return self.hold_ctrl_and_press(options)

  def _get_lines(self,value:list[str]|str,options:AbilityOpts)->str:
    # three kind of line feed count
    prefix_lf:int = options.get('prefix_lf',0)
    segment_lf:int = options.get('segment_lf',0)
    suffix_lf:int = options.get('suffix_lf',0)

    texts:list[str] = value if isinstance(value,list) else [value]
    texts = [str(text) for text in texts]

    if prefix_lf>0:
      texts[0] = '\n'*prefix_lf + texts[0]
    if suffix_lf>0:
      texts[-1] += '\n'*suffix_lf

    lf_chars:str = '\n'*segment_lf if segment_lf>0 else ''
    return lf_chars.join(texts)
