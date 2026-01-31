from typing import Any
from blues_lib.ability.sequence.BaseSeqAbility import BaseSeqAbility
from blues_lib.types.common import AbilityOpts,AbilityDef,OrderOpts,LoopOpts
from blues_lib.deco.ability.ValidateOptions import ValidateOptions
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.ability.sequence.hook.SeqHook import SeqHook

class OrderAbility(BaseSeqAbility):

  @ValidateOptions('order_opts')
  def cast_order(self,options:OrderOpts,bizdata:dict[str,Any]|None=None)->Any:
    '''
    cast the same kind of ability sequence
    Args:
      options (AbilityOpts): the element query options
    Returns:
      Any
    '''
    bizdata = MetaRenderer.render_by_self(bizdata)
    if self._should_skip(options,bizdata):
      return None
    
    hook:SeqHook = SeqHook(self._driver,options,bizdata)
    hook.before()

    # render the total def
    options:OrderOpts = MetaRenderer.render(options,bizdata)
    loop_opts:LoopOpts = options.get('loop')
    method:str = loop_opts.get('method')

    children:list[AbilityOpts]|dict[str,AbilityOpts] = options.get('children')
    if isinstance(children,list):
      atoms:list[AbilityDef] = self._get_atoms_by_list(method,children)
    elif isinstance(children,dict):
      atoms:dict[str,AbilityDef] = self._get_atoms_by_dict(method,children)
    
    result:list[Any]|dict[str,Any]|None = self._exec(atoms)
    
    hook.after()
    return result
  
  def _get_atoms_by_dict(self,method:str,children:dict[str,AbilityOpts])->dict[str,AbilityDef]:
    atoms:dict[str,AbilityDef] = {}
    for k,v in children.items():
      atom:AbilityDef = {
        'name':method,
        'options':v,
      }
      atoms[k] = atom
    return atoms
  
  def _get_atoms_by_list(self,method:str,optset:list[AbilityOpts])->list[AbilityDef]:
    atoms:list[AbilityDef] = []
    for opts in optset:
      atom:AbilityDef = {
        'name':method,
        'options':opts,
      }
      atoms.append(atom)
    return atoms
