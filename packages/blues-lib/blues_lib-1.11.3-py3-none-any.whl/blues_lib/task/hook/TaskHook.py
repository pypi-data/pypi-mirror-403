from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.types.common import TaskHookOpts,TaskDef,AbilityDef,AbilityOpts
from blues_lib.ability.atom.AtomFacade import AtomFacade

class TaskHook:
  def __init__(self,driver:WebDriver,definition:TaskDef,bizdata:dict[str,Any]|None=None):
    self._driver = driver
    validate_tpl = 'except.input.task_hook_opts'
    self._before_opts:TaskHookOpts = MetaRenderer.render_and_validate_node(validate_tpl,'before',definition,bizdata)
    self._after_opts:TaskHookOpts = MetaRenderer.render_and_validate_node(validate_tpl,'after',definition,bizdata)
    self._facade:AtomFacade = None
    self._switch_def:AbilityDef = None
    
  def before(self)->None:
    hook_opts:TaskHookOpts = self._before_opts
    if hook_opts:
      self._switch(hook_opts)
  
  def after(self)->None:
    hook_opts:TaskHookOpts = self._after_opts
    self._switch_back()

  def _switch(self,hook_opts:TaskHookOpts)->None:
    switch_def:AbilityDef = hook_opts.get('switch',{})
    if not switch_def:
      return 

    name:str = switch_def.get('name','')
    options:AbilityOpts = switch_def.get('options',{})
    if not name:
      return 

    self._switch_def = switch_def
    self._facade = AtomFacade(self._driver)
    self._facade.execute(name,options)
    
  def _switch_back(self)->None:
    if not self._facade:
      return

    name:str = self._switch_def.get('name')
    ephemeral:bool = self._switch_def.get('options',{}).get('ephemeral',True)
    window_events:list[str] = ['switch_to_new_tab','switch_to_new_window','switch_to_window']
    if name == 'switch_to_frame':
      self._facade.execute('switch_to_default_content',{})
    elif name in window_events:
      if ephemeral:
        self._facade.execute('close_and_switch_to_first_content')
      else:
        self._facade.execute('switch_to_first_content')
    self._facade = None