from selenium.webdriver.remote.webdriver import WebDriver

# element 
from blues_lib.ability.atom.matcher.ElementTextMatcher import ElementTextMatcher
from blues_lib.ability.atom.matcher.ElementValueMatcher import ElementValueMatcher
from blues_lib.ability.atom.matcher.ElementAttributeMatcher import ElementAttributeMatcher
from blues_lib.ability.atom.matcher.ElementCountMatcher import ElementCountMatcher
from blues_lib.ability.atom.matcher.ElementStateMatcher import ElementStateMatcher
from blues_lib.ability.atom.matcher.UrlMatcher import UrlMatcher

class MatcherAbilityDict():

  @classmethod
  def get(cls,driver:WebDriver)->dict:
    return {
      ElementTextMatcher.__name__:ElementTextMatcher(driver),
      ElementValueMatcher.__name__:ElementValueMatcher(driver),
      ElementAttributeMatcher.__name__:ElementAttributeMatcher(driver),
      ElementCountMatcher.__name__:ElementCountMatcher(driver),
      ElementStateMatcher.__name__:ElementStateMatcher(driver),
      UrlMatcher.__name__:UrlMatcher(driver),
    }