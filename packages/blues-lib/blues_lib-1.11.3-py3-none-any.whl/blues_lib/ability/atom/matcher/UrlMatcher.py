from blues_lib.ability.atom.matcher.MatcherAbility import MatcherAbility
from blues_lib.types.common import AbilityOpts

class UrlMatcher(MatcherAbility):

  def url_to_match(self,options:AbilityOpts)->bool:
    return self._facade.execute('url_matches',options)
