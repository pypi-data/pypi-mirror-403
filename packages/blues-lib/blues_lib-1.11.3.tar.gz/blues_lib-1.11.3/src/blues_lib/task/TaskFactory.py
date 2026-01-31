from typing import Any
from blues_lib.types.common import TaskDef
from blues_lib.dp.factory.Factory import Factory

from blues_lib.task.BaseTask import BaseTask
from blues_lib.task.GenericTask import GenericTask
from blues_lib.task.DriverTask import DriverTask
from blues_lib.task.BrowserTask import BrowserTask

from blues_lib.metastore.validate.MetaValidator import MetaValidator

class TaskFactory(Factory):
  
  _TASKS:dict[str,type[BaseTask]] = {
    GenericTask.__name__:GenericTask,
    DriverTask.__name__:DriverTask,
    BrowserTask.__name__:BrowserTask,
  }
  
  @classmethod
  def create(cls,task_def:TaskDef,task_biz:dict|None=None,ti:Any|None=None,context:dict|None=None)->BaseTask:
    validate_tpl = 'except.input.task_def'
    MetaValidator.validate_with_template(task_def,validate_tpl)

    task_type:str = task_def.get('type')
    task_class:type[BaseTask]|None = cls._TASKS.get(task_type)
    if not task_class:
      error = f"The task '{task_type}' is not supported."
      raise ValueError(f"Failed to create task - {error}")

    return task_class(task_def,task_biz,ti,context)
  