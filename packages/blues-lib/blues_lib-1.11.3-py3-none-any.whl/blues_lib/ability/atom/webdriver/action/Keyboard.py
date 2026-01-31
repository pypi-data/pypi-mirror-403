from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardArrow import KeyboardArrow
from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardSingle import KeyboardSingle
from blues_lib.ability.atom.webdriver.action.keyboard.KeyboardHotkey import KeyboardHotkey
from blues_lib.types.common import AbilityOpts

class Keyboard(KeyboardArrow,KeyboardSingle,KeyboardHotkey):
  """
  A representation of any key input device for interacting with a web page.
  Reference : https://www.selenium.dev/documentation/webdriver/actions_api/keyboard/
  """
  
  def paste_and_enter(self,options:AbilityOpts)->bool:
    self.paste(options)
    return self.enter(options)

  def clear_paste_and_enter(self,options:AbilityOpts)->bool:
    self.clear_and_paste(options)
    return self.enter(options)

  
