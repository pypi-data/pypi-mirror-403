from blues_lib.dp.executor.Executor import Executor
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.task.TaskFactory import TaskFactory
from blues_lib.task.BaseTask import BaseTask
from blues_lib.metastore.validate.MetaValidator import MetaValidator
from blues_lib.flow.MockTI import MockTI

class Flow(Executor):
  
  def __init__(self,dag_def:dict,dag_biz:list[dict],context:dict|None=None): 
    super().__init__()
    self._task_ids:list[str] = []
    self._dag_def:dict = dag_def
    self._dag_biz:list[dict] = dag_biz or []
    self._context = context
    
  @property
  def dag_id(self)->str:
    return self._dag_def.get('dag_id')

  @property
  def dag_def(self)->dict:
    return self._dag_def

  @property
  def dag_biz(self)->list[dict]:
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

    executors:list[Executor] = self._get_executors()
    for executor in executors:
      self._logger.info(f'Task {executor.task_id} started')
      self._task_ids.append(executor.task_id)
      executor.execute()

    return STDOut(200,f'flow success : {"->".join(self._task_ids)}')
        
  def _get_executors(self)->list[Executor]:
    executors:list[Executor] = []
    task_defs:list[dict] = self._dag_def.get('tasks')
    for idx,task_def in enumerate(task_defs):
      bizdata = self._dag_biz[idx] if idx < len(self._dag_biz) else {}
      self._add_task(executors,task_def,bizdata)
    return executors
    
  def _add_task(self,executors:list[Executor],task_def:dict)->Executor:
    ti = MockTI(task_def.get('task_id'))
    task_type:str = task_def.get('type')
    executor:BaseTask = TaskFactory.create(task_type,ti,self._context)
    executors.append(executor)
