from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.matcher.MatcherAbility import MatcherAbility
from blues_lib.types.common import AbilityOpts

class ElementValueMatcher(MatcherAbility):

  def element_value_to_equal(self,options:AbilityOpts)->bool:
    value:str = self._get_element_value(options)
    expected:str = str(options.get('expected')).strip()
    matched:bool = value==expected
    return self._raise_or_return(options,matched,'element_value_to_equal',value,expected)

  def element_value_to_match(self,options:AbilityOpts)->bool:
    value:str = self._get_element_value(options)
    expected:str = str(options.get('expected')).strip()
    matched:bool = bool(re.search(expected,value))
    return self._raise_or_return(options,matched,'element_value_to_match',value,expected)

  def _get_element_value(self,options:AbilityOpts)->str:
    elem:WebElement|None = self._facade.execute('query_element',options)
    return elem.get_attribute('value').strip() if elem else ''