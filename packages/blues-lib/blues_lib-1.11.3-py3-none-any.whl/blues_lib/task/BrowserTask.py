from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.metastore.validate.MetaValidator import MetaValidator
from blues_lib.types.common import AbilityDef,SeqDef,TaskDef,DriverDef,DriverMode
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.ability.AbilityExecutor import AbilityExecutor
from blues_lib.task.BaseTask import BaseTask
from blues_lib.task.driver.DriverInitializer import DriverInitializer
from blues_lib.task.hook.TaskHook import TaskHook

class BrowserTask(BaseTask):

  def _prepare(self,definition:TaskDef,bizdata:dict|None=None)->None:
    self._driver_def:DriverDef = MetaRenderer.render_node('driver',definition,bizdata)
    mode:DriverMode = self._driver_def.get('mode')
    if mode == 'context':
      if self._context is None:
        raise ValueError(f"{self.__class__.__name__} context is required for BrowserTask with mode {mode}")
      self._driver = self._context.get('driver')
    else:
      self._driver = DriverInitializer(self._driver_def,bizdata).init()

    if not self._driver or not isinstance(self._driver,WebDriver):
      raise ValueError(f"{self.__class__.__name__} failed to create the [{mode}] driver")

  def _process(self,definition:TaskDef,bizdata:dict|None=None)->list[Any]|dict[str,Any]|None:
    self._prepare(definition,bizdata)
    
    hook:TaskHook = TaskHook(self._driver,definition,bizdata)
    hook.before()

    validate_tpl = 'except.input.ability_def_col'
    abilities:list[AbilityDef|SeqDef]|dict[str,AbilityDef|SeqDef] = MetaValidator.validate_node_with_template('abilities',definition,validate_tpl)

    try:
      results:list[Any]|dict[str,Any] = AbilityExecutor(self._driver).execute(abilities,bizdata)
      
      hook.after()
      
      self._quit_by_mode()
      return results
    except Exception as e:
      self._quit()
      raise
    
  def _quit_by_mode(self):
    mode:DriverMode = self._driver_def.get('mode')
    if mode == 'context':
      ephemeral:bool = self._driver_def.get('ephemeral',False)
    else:
      ephemeral:bool = self._driver_def.get('ephemeral',True)
    if ephemeral:
      self._quit()

  def _quit(self):
    if self._driver:
      self._driver.quit()
      