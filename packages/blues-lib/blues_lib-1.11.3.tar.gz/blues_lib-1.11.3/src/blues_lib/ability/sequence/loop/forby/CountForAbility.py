from typing import Any
from blues_lib.ability.sequence.loop.forby.BaseForAbility import BaseForAbility
from blues_lib.types.common import SeqOpts,LoopOpts

class CountForAbility(BaseForAbility):
  """
  loop by each count and execute the ability sequence
  """

  def cast_for_by_count(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    return self._cast_for(options,bizdata)
  
  def _get_loop_items(self,loop_opts:LoopOpts)->list[dict[str,Any]]:
    count:int = int(loop_opts.get('count') or 0)
    if not count:
      raise ValueError('for loop by count must be a count greater than 0')
    return [{'count':i} for i in range(count)]
