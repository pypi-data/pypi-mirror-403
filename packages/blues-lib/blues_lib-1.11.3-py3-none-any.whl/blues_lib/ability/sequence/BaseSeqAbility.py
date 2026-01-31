import logging
from abc import ABC
from typing import Any
from selenium.webdriver.chrome.webdriver import WebDriver 
from blues_lib.ability.atom.AtomFacade import AtomFacade
from blues_lib.types.common import AbilityOpts,AbilityDef,SeqOpts,AbilityCondition
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.dp.exception.matcher.MatchedBreakException import MatchedBreakException
from blues_lib.dp.exception.matcher.UnmatchedBreakException import UnmatchedBreakException
from blues_lib.deco.ability.ValidateOptions import ValidateOptions

class BaseSeqAbility(ABC):

  def __init__(self,driver:WebDriver):
    self._driver = driver
    self._facade = AtomFacade(driver)
    self._logger = logging.getLogger('airflow.task')

  @ValidateOptions('ability_def_col')
  def _exec(self,atoms:list[AbilityDef]|dict[str,AbilityDef])->list[Any]|dict[str,Any]|None:
    '''
    Use abilities of a series of elements in order
    Args:
      atoms (list[AbilityDef]|dict[str,AbilityDef]): the atom ability list or dict
    Returns:
      list[Any]|dict[str,Any]|None
    '''
    
    # calculate results
    results:list[Any]|dict[str,Any]|None = None
    if isinstance(atoms,list):
      results = self._exec_by_list(atoms)
    elif isinstance(atoms,dict):
      results = self._exec_by_dict(atoms)
    return results
  
  def _exec_by_dict(self,atoms:dict[str,AbilityDef])->dict[str,Any]:
    results:dict[str,Any] = {}
    for key,atom in atoms.items():
      success,result = self._exec_and_catch(atom)
      results[key] = result
      if not success:
        break
    return results

  def _exec_by_list(self,atoms:list[AbilityDef])->list[Any]:
    results:list[Any] = []
    for atom in atoms:
      success,result = self._exec_and_catch(atom)
      results.append(result)
      if not success:
        break
    return results
  
  def _should_skip(self,options:SeqOpts,bizdata:dict[str,Any]|None=None)->bool:
    condition:AbilityCondition = MetaRenderer.render_node('condition',options,bizdata)
    if 'skip_if' in condition and condition['skip_if']:
      self._logger.info(f"{self.__class__.__name__} skip_if condition is True, skip the sequence")
      return True
    if 'skip_unless' in condition and not condition['skip_unless']:
      self._logger.info(f"{self.__class__.__name__} skip_unless condition is False, skip the sequence")
      return True
    return False
  
  @ValidateOptions('ability_def')
  def _exec_and_catch(self,atom:AbilityDef)->tuple[str,Any|None]:
    result:Any|None = None
    try:
      result = self._exec_ability(atom)
      return True,result
    except MatchedBreakException as e:
      self._logger.warning(e)
      return False,True
    except UnmatchedBreakException as e:
      self._logger.warning(e)
      return False,False

  def _exec_ability(self,atom:AbilityDef)->Any:
    name:str = atom.get('name')
    opts:AbilityOpts = atom.get('options')
    args:list[Any] = [name,opts] if opts else [name]
    return self._facade.execute(*args)
