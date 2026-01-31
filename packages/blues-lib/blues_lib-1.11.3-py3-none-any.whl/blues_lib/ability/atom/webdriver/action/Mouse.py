from blues_lib.ability.atom.webdriver.action.mouse.MouseClick import MouseClick
from blues_lib.ability.atom.webdriver.action.mouse.MouseMove import MouseMove
from blues_lib.ability.atom.webdriver.action.mouse.MouseDrag import MouseDrag

class Mouse(MouseClick,MouseMove,MouseDrag):
  """
  Mouse class to perform mouse actions.
    If the element is outside the viewable window, 
    The element will automatically roll into the window, 
  Reference : https://www.selenium.dev/documentation/webdriver/interactions/mouse/
  """
  
  pass
  