from typing import Any
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.sequence.loop.EachAbility import EachAbility
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.types.common import AbilityOpts,SeqOpts,LoopOpts,AbilityDef
from blues_lib.deco.ability.ValidateOptions import ValidateOptions
from blues_lib.ability.sequence.hook.SeqHook import SeqHook

class PageAbility(EachAbility):

  @ValidateOptions('seq_opts')
  def cast_page(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    '''
    loop by each page elements and execute the ability sequence
    Args:
      options (SeqOpts): the sequence options
    Returns:
      list[list|dict]: the results of the abilities
    '''
    bizdata = MetaRenderer.render_by_self(bizdata)
    if self._should_skip(options,bizdata):
      return None
    
    hook:SeqHook = SeqHook(self._driver,options,bizdata)
    hook.before()

    validate_tpl = 'except.input.loop_page_opts'
    loop_opts:LoopOpts = MetaRenderer.render_and_validate_node(validate_tpl,'loop',options,bizdata)
    
    page_elems:list[WebElement] = self._query_page_elems(loop_opts)

    max_attempts:int = int(loop_opts.get('max_attempts') or -1)
    each_opts:AbilityOpts|None = loop_opts.get('each')
    totals:list[list|dict] = []

    for idx,elem in enumerate(page_elems):
      if max_attempts>0 and idx>=max_attempts:
        break
      if idx>0:
        self._next_page(elem)

      if idx>0:
        self._sleep_by_interval(loop_opts)

      results:list[list|dict] = self._exec_or_cast_each(each_opts,options,bizdata)
      totals+=results

    self._log('page',idx,len(totals))
    
    hook.after()
    return totals

  def _query_page_elems(self,loop_opts:LoopOpts) -> list[WebElement]:
    opts:AbilityOpts = loop_opts.get('page')
    elems:list[WebElement]|None = self._facade.execute('query_elements',opts)
    if not elems:
      raise ValueError(f'page loop options {opts} query no elements')
    return elems

  def cast_next(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    bizdata = MetaRenderer.render_by_self(bizdata)
    if self._should_skip(options,bizdata):
      return None
    
    hook:SeqHook = SeqHook(self._driver,options,bizdata)
    hook.before()

    validate_tpl = 'except.input.loop_next_opts'
    loop_opts:LoopOpts = MetaRenderer.render_and_validate_node(validate_tpl,'loop',options,bizdata)
    
    max_attempts:int = int(loop_opts.get('max_attempts') or -1)
    each_opts:AbilityOpts|None = loop_opts.get('each')

    # execute once before loop
    totals:list[list|dict] = self._exec_or_cast_each(each_opts,options,bizdata)

    idx:int = 1
    while True:
      if max_attempts>0 and idx>=max_attempts:
        break

      elem:WebElement|None = self._query_next_elem(loop_opts)
      if not elem:
        break

      self._sleep_by_interval(loop_opts)

      # click to open the next page
      self._next_page(elem)

      totals+= self._exec_or_cast_each(each_opts,options,bizdata)
      idx+=1

    self._log('next',idx,len(totals))
    
    hook.after()
    return totals
  
  def _query_next_elem(self,loop_opts:LoopOpts) -> WebElement|None:
    opts:AbilityOpts = loop_opts.get('next')
    return self._facade.execute('query_element',opts)

  def _next_page(self,elem:WebElement):
    self._facade.execute('click',{'target':elem})
    
  def _exec_or_cast_each(self,each_opts:AbilityOpts|None,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    if each_opts:
      return self.cast_each(options,bizdata)
    else:
      atoms:list[AbilityDef]|dict[str,AbilityDef] = MetaRenderer.render_node('children',options,bizdata)
      return [self._exec(atoms)]
