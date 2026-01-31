from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.matcher.MatcherAbility import MatcherAbility
from blues_lib.types.common import AbilityOpts

class ElementCountMatcher(MatcherAbility):

  def element_count_to_be_equal(self,options:AbilityOpts)->bool:
    value:int = self._get_element_count(options)
    expected:int = int(options.get('expected'))
    matched:bool = value==expected
    return self._raise_or_return(options,matched,'element_count_to_be_equal',value,expected)

  def element_count_to_be_greater_than(self,options:AbilityOpts)->bool:
    value:int = self._get_element_count(options)
    expected:int = int(options.get('expected'))
    matched:bool = value>expected
    return self._raise_or_return(options,matched,'element_count_to_be_greater_than',value,expected)

  def element_count_to_be_less_than(self,options:AbilityOpts)->bool:
    value:int = self._get_element_count(options)
    expected:int = int(options.get('expected'))
    matched:bool = value<expected
    return self._raise_or_return(options,matched,'element_count_to_be_less_than',value,expected)
  
  def _get_element_count(self,options:AbilityOpts)->int:
    elems:list[WebElement]|None = self._facade.execute('query_elements',options)
    return len(elems) if elems else 0
