from typing import Any
from blues_lib.ability.sequence.loop.forby.BaseForAbility import BaseForAbility
from blues_lib.types.common import SeqOpts,LoopOpts

class ItemForAbility(BaseForAbility):
  """
  loop by each items and execute the ability sequence
  """

  def cast_for_by_item(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    return self._cast_for(options,bizdata)
  
  def _get_loop_items(self,loop_opts:LoopOpts)->list[dict[str,Any]]:
    items:list[dict[str,Any]] = loop_opts.get('items')
    if not items or not isinstance(items,list):
      raise ValueError('for by item loop items must be a non-empty list')
    return items
