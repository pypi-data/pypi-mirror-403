from typing import Any
from blues_lib.ability.sequence.BaseSeqAbility import BaseSeqAbility
from blues_lib.types.common import SeqOpts,AbilityDef
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.deco.ability.ValidateOptions import ValidateOptions
from blues_lib.ability.sequence.hook.SeqHook import SeqHook

class StandardSeqAbility(BaseSeqAbility):

  @ValidateOptions('seq_opts')
  def cast(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[Any]|dict[str,Any]|None:
    bizdata = MetaRenderer.render_by_self(bizdata)
    if self._should_skip(options,bizdata):
      return None
    
    hook:SeqHook = SeqHook(self._driver,options,bizdata)
    hook.before()

    atoms:list[AbilityDef]|dict[str,AbilityDef] = MetaRenderer.render_node('children',options,bizdata)
    result:list[Any]|dict[str,Any]|None = self._exec(atoms)

    hook.after()
    return result
