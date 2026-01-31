from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.matcher.MatcherAbility import MatcherAbility
from blues_lib.types.common import AbilityOpts

class ElementAttributeMatcher(MatcherAbility):

  def element_attribute_to_equal(self,options:AbilityOpts)->bool:
    value:str = self._get_element_attribute(options)
    expected:str = str(options.get('expected')).strip()
    matched:bool = value==expected
    return self._raise_or_return(options,matched,'element_attribute_to_equal',value,expected)

  def element_attribute_to_match(self,options:AbilityOpts)->bool:
    value:str = self._get_element_attribute(options)
    expected:str = str(options.get('expected')).strip()
    matched:bool = bool(re.match(expected,value))
    return self._raise_or_return(options,matched,'element_attribute_to_match',value,expected)

  def _get_element_attribute(self,options:AbilityOpts)->str:
    elem:WebElement|None = self._facade.execute('query_element',options)
    return elem.get_attribute(options.get('value')).strip() if elem else ''