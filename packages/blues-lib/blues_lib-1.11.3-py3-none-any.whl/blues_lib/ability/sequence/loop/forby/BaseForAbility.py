from abc import abstractmethod
from typing import Any
from blues_lib.ability.sequence.loop.LoopAbility import LoopAbility
from blues_lib.metastore.biz.BizManager import BizManager
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.types.common import SeqOpts,LoopOpts,AbilityDef
from blues_lib.deco.ability.ValidateOptions import ValidateOptions
from blues_lib.ability.sequence.hook.SeqHook import SeqHook

class BaseForAbility(LoopAbility):
  """
  loop by each items and execute the ability sequence
  """

  @ValidateOptions('seq_opts')
  def _cast_for(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    """
    loop by each items and execute the ability sequence
    Args:
      options (SeqOpts): the sequence options
    Returns:
      list[list|dict]: the results of the abilities
    """
    bizdata = MetaRenderer.render_by_self(bizdata)
    if self._should_skip(options,bizdata):
      return None
    
    hook:SeqHook = SeqHook(self._driver,options,bizdata)
    hook.before()

    validate_tpl = 'except.input.loop_for_opts'
    loop_opts:LoopOpts = MetaRenderer.render_and_validate_node(validate_tpl,'loop',options,bizdata)

    results:list[list|dict] = []
    max_attempts:int = int(loop_opts.get('max_attempts') or 0)

    items:list[dict[str,Any]] = self._get_loop_items(loop_opts)
    for idx,item in enumerate(items):

      if max_attempts>0 and idx>=max_attempts:
        break

      if idx>0:
        self._sleep_by_interval(loop_opts)
      
      result:list[Any]|dict[str,Any] = self._handle_single_cast(options,item,idx,bizdata)
      results.append(result)

    self._log('for',len(items),len(results))
    
    hook.after()
    return results
  
  def _handle_single_cast(self,options:SeqOpts,item:dict[str,Any],idx:int,bizdata:dict[str,Any])->list[Any]|dict[str,Any]:
    iter_bizdata:dict[str,Any] = BizManager.add_item(bizdata,item,idx)
    atoms:list[AbilityDef]|dict[str,AbilityDef] = MetaRenderer.render_node('children',options,iter_bizdata)
    return self._exec(atoms)

  @abstractmethod
  def _get_loop_items(self,loop_opts:LoopOpts)->list[dict[str,Any]]:
    pass