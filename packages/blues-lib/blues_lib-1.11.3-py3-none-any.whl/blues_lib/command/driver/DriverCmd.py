import logging
from typing import Any
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.types.common import DriverCmdDef,AbilityDef,SeqDef,DriverOpts
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.schema.SchemaValidator import SchemaValidator
from blues_lib.ability.AbilityExecutor import AbilityExecutor
from blues_lib.command.driver.DriverCreater import DriverCreater
from blues_lib.command.driver.OutputCreater import OutputCreater

class DriverCmd:

  def __init__(self,cmd_def:DriverCmdDef,bizdata:dict|None=None)->None:
    # replace env function include vars
    self._bizdata = MetaRenderer.render_by_self(bizdata)
    self._logger = logging.getLogger('airflow.task')
    
    self._cmd_def = cmd_def
    self._driver_opts:DriverOpts = MetaRenderer.render_node('driver',cmd_def,self._bizdata)
    self._driver = DriverCreater.create(self._driver_opts,self._bizdata)

  def execute(self)->STDOut:

    tpl_path = 'except.input.driver_cmd_def'
    stat,message = SchemaValidator.validate_with_template(self._cmd_def,tpl_path)
    if not stat:
      raise ValueError(message)
    
    executor = AbilityExecutor(self._driver)
    abilities:list[AbilityDef|SeqDef]|dict[str,AbilityDef|SeqDef] = self._cmd_def['abilities']
    try:
      results:list[Any]|dict[str,Any] = executor.execute(abilities,self._bizdata)
      # auto quit driver
      self._auto_quit()
      return OutputCreater.resolve(results)
    except Exception as e:
      self._driver.quit()
      return OutputCreater.reject(str(e))

  def _auto_quit(self):
    driver_opts:DriverOpts = self._driver_opts or {}
    if driver_opts.get('auto_quit',True):
      self._driver.quit()
