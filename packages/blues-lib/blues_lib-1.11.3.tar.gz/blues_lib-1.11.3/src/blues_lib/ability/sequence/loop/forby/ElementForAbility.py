from typing import Any
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.sequence.loop.forby.BaseForAbility import BaseForAbility
from blues_lib.types.common import SeqOpts,LoopOpts,AbilityOpts

class ElementForAbility(BaseForAbility):
  """
  loop by each items and execute the ability sequence
  """

  def cast_for_by_element(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->list[list|dict]:
    return self._cast_for(options,bizdata)
  
  def _get_loop_items(self,loop_opts:LoopOpts)->list[dict[str,Any]]:
    elem_opts:AbilityOpts = loop_opts.get('element')
    elems:list[WebElement] = self._facade.execute('query_elements',elem_opts)
    if not elems:
      raise ValueError('for by element loop elements must be a non-empty list')
    return [{'element':elem} for elem in elems]
