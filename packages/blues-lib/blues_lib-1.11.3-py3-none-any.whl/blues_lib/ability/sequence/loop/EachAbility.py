import time
from typing import Any
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.sequence.loop.LoopAbility import LoopAbility
from blues_lib.metastore.biz.BizManager import BizManager
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.types.common import AbilityOpts,SeqOpts,AbilityDef,LoopOpts
from blues_lib.deco.ability.ValidateOptions import ValidateOptions
from blues_lib.ability.sequence.hook.SeqHook import SeqHook

class EachAbility(LoopAbility):

  @ValidateOptions('seq_opts')
  def cast_each(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    """
    loop by each elements and execute the ability sequence
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

    # render and validate
    validate_tpl = 'except.input.loop_each_opts'
    loop_opts:LoopOpts = MetaRenderer.render_and_validate_node(validate_tpl,'loop',options,bizdata)

    loop_elems:list[WebElement] = self._query_loop_elems(loop_opts)

    results:list[list|dict] = []
    for idx,elem in enumerate(loop_elems):

      if idx>0:
        self._sleep_by_interval(loop_opts)

      result:list[Any]|dict[str,Any] = self._handle_single_cast(options,elem,idx,bizdata)
      results.append(result)

    self._log('each',len(loop_elems),len(results))

    hook.after()
    return results
  
  def _query_loop_elems(self,loop_opts:LoopOpts) -> list[WebElement]:
    opts:AbilityOpts = loop_opts.get('each')
    elems:list[WebElement]|None = self._facade.execute('query_elements',opts)
    if not elems:
      raise ValueError(f'each loop options {opts} query no elements')
    return elems
  
  def _handle_single_cast(self,options:SeqOpts,elem:WebElement,idx:int,bizdata:dict[str,Any]) -> list[Any]|dict[str,Any]:
    self._append_loop_elem(options,elem)
    # create a each bizdata copy and pass to the cast sequence
    iter_bizdata:dict[str,Any] = BizManager.add_index(bizdata,idx)
    atoms:list[AbilityDef]|dict[str,AbilityDef] = MetaRenderer.render_node('children',options,iter_bizdata)
    # continue pass the origin options
    return self._exec(atoms)

  def _append_loop_elem(self,options:AbilityOpts,elem:WebElement):
    """
    Replace the root element by the loop element for the abilities
    Args:
      options (AbilityOpts): the ability options
      elem (WebElement): the element
    """
    atoms:list[AbilityDef]|dict[str,AbilityDef] = options.get('children')
    if isinstance(atoms,list):
      for atom in atoms:
        self._update_options(atom['options'],elem)
    elif isinstance(atoms,dict):
      for atom in atoms.values():
        self._update_options(atom['options'],elem)

  def _update_options(self,options:AbilityOpts,elem:WebElement):
    if options.get('target'):
      options['root'] = elem
    else:
      # the each element is the ability's element
      options['target'] = elem
