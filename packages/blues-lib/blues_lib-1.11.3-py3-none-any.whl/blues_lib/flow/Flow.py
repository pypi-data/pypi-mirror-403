from blues_lib.dp.executor.Executor import Executor
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.task.TaskFactory import TaskFactory
from blues_lib.task.BaseTask import BaseTask
from blues_lib.metastore.validate.MetaValidator import MetaValidator
from blues_lib.flow.MockTI import MockTI
from blues_lib.types.common import TaskDef,FlowDef,FlowBiz

class Flow(Executor):
  
  def __init__(self,dag_def:FlowDef,dag_biz:FlowBiz,context:dict|None=None): 
    super().__init__()
    self._dag_def = dag_def
    self._dag_biz = dag_biz
    self._task_ids = []
    self._context = context or {}
    
  @property
  def dag_id(self)->str:
    return self._dag_def.get('dag_id')

  @property
  def dag_def(self)->FlowDef:
    return self._dag_def

  @property
  def dag_biz(self)->FlowBiz:
    return self._dag_biz
  
  @property
  def last_task_output(self)->dict:
    return self.get_task_output(self.task_ids[-1])
    
  @property
  def size(self)->int:
    return len(self._task_ids)

  @property
  def task_ids(self)->list[str]:
    return self._task_ids
    
  def get_task_output(self,task_id:str)->dict:
    return MockTI.store.get(task_id) or {}
  
  def execute(self)->STDOut:
    validate_tpl = 'except.input.flow_def'
    MetaValidator.validate_with_template(self._dag_def,validate_tpl)
    validate_tpl = 'except.input.flow_biz'
    MetaValidator.validate_with_template(self._dag_biz,validate_tpl)

    executors:list[BaseTask] = self._get_executors()
    for executor in executors:
      self._logger.info(f'Task {executor.task_id} started')
      executor.execute()

    return STDOut(200,f'flow success : {"->".join(self._task_ids)}',self.last_task_output)
        
  def _get_executors(self)->list[BaseTask]:
    executors:list[BaseTask] = []
    task_defs:list[TaskDef] = self._dag_def.get('tasks')
    task_bizs:list[dict] = self._dag_biz.get('tasks') or []
    for idx,task_def in enumerate(task_defs):
      self._append_executor(executors,idx,task_def,task_bizs)
    return executors
  
  def _append_executor(self,executors:list[BaseTask],idx:int,task_def:TaskDef,task_bizs:list[dict])->None:
    task_id:str = task_def.get('task_id')
    if task_id in self._task_ids:
      raise ValueError(f"task_id {task_id} is duplicated")

    task_biz:dict = task_bizs[idx] if idx < len(task_bizs) else {}
    ti = MockTI(task_id)
    executor:BaseTask = TaskFactory.create(task_def,task_biz,ti,self._context)
    self._task_ids.append(task_id)
    executors.append(executor)
    
