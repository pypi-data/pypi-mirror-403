from blues_lib.ability.atom.BaseAbility import BaseAbility
from blues_lib.types.common import AbilityOpts
from blues_lib.util.BluesDateTime import BluesDateTime

class Util(BaseAbility):
  
  def sleep(self,options:AbilityOpts)->bool:
    duration:float|int = float(options.get('duration') or 0)
    if duration>0:
      value:str = options.get('value') or f'Sleep {duration} seconds'
      BluesDateTime.count_down({
        "duration":duration,
        "title":value,
      })
    return True