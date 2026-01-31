import logging
from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.ability.AbilityFacade import AbilityFacade
from blues_lib.types.common import AbilityOpts,SeqOpts,AbilityDef,SeqDef
from blues_lib.dp.exception.matcher.MatchedBreakException import MatchedBreakException
from blues_lib.dp.exception.matcher.UnmatchedBreakException import UnmatchedBreakException
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.deco.ability.ValidateOptions import ValidateOptions

class AbilityExecutor:
  # execute ability or seq and return STDOut
  
  def __init__(self,driver:WebDriver|None=None)->None:
    self._driver = driver
    self._facade = AbilityFacade(driver)
    self._logger = logging.getLogger('airflow.task')
  
  @ValidateOptions('ability_def_col')
  def execute(self,abilities:list[AbilityDef|SeqDef]|dict[str,AbilityDef|SeqDef],bizdata:dict[str,Any]|None=None)->list[Any]|dict[str,Any]:

    bizdata = MetaRenderer.render_by_self(bizdata)
    results:list[Any]|dict[str,Any] = []    
    if isinstance(abilities,dict):
      results = self._exec_by_dict(abilities,bizdata)
    elif isinstance(abilities,list):
      results = self._exec_by_list(abilities,bizdata)
    return results
    
  def _get_ability_args(self,atom:AbilityDef|SeqDef,bizdata:dict[str,Any]|None=None)->list[Any]|None:
      # name don't support use bizdata's variable
    name:str = atom.get('name')
    options:AbilityOpts|SeqOpts = atom.get('options')
    is_seq_method:bool = 'cast' in name
    if not name:
      self._logger.warning(f'ability {name} name is None')
      return None

    if is_seq_method:
      return self._get_seq_args(name,options,bizdata)
    else:
      return self._get_atom_args(name,options,bizdata)
    
  def _get_seq_args(self,name:str,options:SeqOpts|None,bizdata:dict[str,Any]|None=None)->list[Any]|None:
    if not options:
      self._logger.warning(f'seq {name} options is None')
      return None
    # pass the bizdata and the original options
    return [name,options,bizdata]
  
  def _get_atom_args(self,name:str,options:AbilityOpts|None,bizdata:dict[str,Any]|None=None)->list[Any]:
    validate_tpl = 'except.input.ability_opts'
    options = MetaRenderer.render_and_validate(validate_tpl,options,bizdata)
    return [name,options] if options else [name]
 
  def _exec_by_dict(self,abilities:dict[str,AbilityDef|SeqDef],bizdata:dict[str,Any]|None=None)->dict[str,Any]:
    results:dict[str,Any] = {}
    for key,atom in abilities.items():
      success,result = self._exec_and_catch(atom,bizdata)
      results[key] = result
      if not success:
        break
    return results

  def _exec_by_list(self,abilities:list[AbilityDef|SeqDef],bizdata:dict[str,Any]|None=None)->list[Any]:
    results:list[Any] = []
    for atom in abilities:
      success,result = self._exec_and_catch(atom,bizdata)
      results.append(result)
      if not success:
        break
    return results
  
  def _exec_and_catch(self,atom:AbilityDef|SeqDef,bizdata:dict[str,Any]|None=None)->tuple[bool,Any|None]:
    args:list[Any]|None = self._get_ability_args(atom,bizdata)
    if not args:
      self._logger.warning(f'ability {atom} args is None')
      return False,None
    try:
      return True,self._facade.execute(*args)
    except MatchedBreakException as e:
      self._logger.warning(e)
      return False,True
    except UnmatchedBreakException as e:
      self._logger.warning(e)
      return False,False
