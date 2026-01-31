from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.matcher.MatcherAbility import MatcherAbility
from blues_lib.types.common import AbilityOpts

class ElementStateMatcher(MatcherAbility):

  def element_to_be_visible(self,options:AbilityOpts)->bool:
    elem:WebElement|None = self._facade.execute('visibility_of_element_located',options)
    value:bool = bool(elem)
    expected:bool = True
    matched:bool = value==expected
    return self._raise_or_return(options,matched,'element_to_be_visible',value,expected)
