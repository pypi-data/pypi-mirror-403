from blues_lib.ability.atom.webdriver.element.interaction.InterInput import InterInput
from blues_lib.ability.atom.webdriver.element.interaction.InterSelect import InterSelect
from blues_lib.ability.atom.webdriver.element.interaction.InterCheck import InterCheck
from blues_lib.ability.atom.webdriver.element.interaction.InterChoice import InterChoice
from blues_lib.ability.atom.webdriver.element.interaction.InterClick import InterClick

class Interaction(InterSelect,InterCheck,InterInput,InterChoice,InterClick):
  """
  A high-level instruction set for manipulating form controls.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/interactions/

  It attempts to perform two things before attempting the specified action.
  1. If it determines the element is outside the viewport, it scrolls the element into view, specifically it will align the bottom of the element with the bottom of the viewport.
  2. It ensures the element is interactable before taking the action. 
  """
