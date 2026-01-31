import logging
from abc import ABC,abstractmethod
from typing import Any
from blues_lib.types.common import TaskDef
from blues_lib.metastore.validate.MetaValidator import MetaValidator
from blues_lib.task.input.InputHandler import InputHandler
from blues_lib.task.output.OutputHandler import OutputHandler
from blues_lib.flow.MockTI import MockTI

class BaseTask(ABC):

  def __init__(self,task_def:TaskDef,task_biz:dict|None=None,ti:Any|None=None,context:dict|None=None)->None:
    self._task_def = task_def
    self._task_biz = task_biz or {}
    self._ti = ti or MockTI(f'{self.__class__.__name__}_ti')
    self._context = context 
    self._logger = logging.getLogger('airflow.task')
  
  @property
  def task_id(self)->str:
    return self._task_def.get('task_id')

  def execute(self)->None:
    definition,bizdata = self._setup(self._task_def,self._task_biz)
    results:list[Any]|dict[str,Any] = self._process(definition,bizdata)
    self._teardown(results)

  @abstractmethod   
  def _process(self,definition:TaskDef,bizdata:dict|None=None)->list[Any]|dict[str,Any]:
    pass
  
  def _setup(self,definition:TaskDef,bizdata:dict)->tuple[TaskDef,dict|None]:
    definition,bizdata = InputHandler.handle(definition,bizdata,self._ti)
    # validate after input handler
    validate_tpl = 'except.input.task_def'
    MetaValidator.validate_with_template(definition,validate_tpl)
    return definition,bizdata
  
  def _teardown(self,results:list[Any]|dict[str,Any])->None:
    OutputHandler.push_to_xcom(self._ti,results) 
