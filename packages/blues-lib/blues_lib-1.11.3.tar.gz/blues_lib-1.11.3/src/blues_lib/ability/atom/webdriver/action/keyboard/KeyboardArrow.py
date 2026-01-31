from selenium.webdriver.common.keys import Keys
from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardBase import KeyboardBase
from blues_lib.types.common import AbilityOpts

class KeyboardArrow(KeyboardBase):

  def arrow_up(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the arrow up key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.ARROW_UP
    return self.press(options)

  def arrow_down(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the arrow down key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.ARROW_DOWN
    return self.press(options)
  
  def arrow_left(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the arrow left key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.ARROW_LEFT
    return self.press(options)

  def arrow_right(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the arrow right key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.ARROW_RIGHT
    return self.press(options)

  def page_up(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the page up key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.PAGE_UP
    return self.press(options)

  def page_down(self,options:AbilityOpts|None=None)->bool:
    '''
    Press the page down key
    Args:
      options (AbilityOpts): The element query options
    '''
    options = options or {}
    options['value'] = Keys.PAGE_DOWN
    return self.press(options)
