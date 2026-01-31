from selenium.webdriver.common.keys import Keys
from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardBase import KeyboardBase
from blues_lib.types.common import AbilityOpts

class KeyboardSingle(KeyboardBase):

  def enter(self,options:AbilityOpts)->bool:
    """
    Press the enter key
    Args:
      options (AbilityOpts): The element query options
    """
    key_options = {'value':Keys.ENTER}
    options = {**options,**key_options}
    return self.press(options)
  
  def newline(self,options:AbilityOpts)->bool:
    """
    Press the newline key
    Args:
      options (AbilityOpts): The element query options
    """
    key_options = {'value':'\n'}
    options = {**options,**key_options}
    return self.press(options)
  
  def esc(self,options:AbilityOpts|None=None)->bool:
    """
    Press the escape key
    Args:
      options (AbilityOpts): The element query options
    """
    key_options = {'value':Keys.ESCAPE}
    options = {**options,**key_options} or key_options
    return self.press(options)

  def f12(self,options:AbilityOpts|None=None)->bool:
    """
    Press the f12 key
    """
    key_options = {'value':Keys.F12}
    options = {**options,**key_options} or key_options
    return self.press(options)
  