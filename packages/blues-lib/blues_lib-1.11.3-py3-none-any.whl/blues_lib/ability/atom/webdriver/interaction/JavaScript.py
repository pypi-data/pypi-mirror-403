from blues_lib.ability.atom.webdriver.interaction.javascript.JSDocument import JSDocument
from blues_lib.ability.atom.webdriver.interaction.javascript.JSCss import JSCss
from blues_lib.ability.atom.webdriver.interaction.javascript.JSLoader import JSLoader
from blues_lib.ability.atom.webdriver.interaction.javascript.JSScroll import JSScroll

from blues_lib.types.common import AbilityOpts

class JavaScript(JSDocument,JSCss,JSLoader,JSScroll):
  """
  JavaScript class to execute javascript.
  Reference : https://www.selenium.dev/documentation/webdriver/interactions/windows/#execute-script
  """
  
  def display_and_scroll_into_view(self,options:AbilityOpts)->bool:
    """
    Display the element and scroll it into view.
    Args:
      options (AbilityOpts): The options for the element to display and scroll into view.
    Returns:
      bool
    """
    self.display(options)
    return self.scroll_into_view(options)
  