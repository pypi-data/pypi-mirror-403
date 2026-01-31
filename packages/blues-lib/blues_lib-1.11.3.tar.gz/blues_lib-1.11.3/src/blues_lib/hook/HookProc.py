from abc import abstractmethod
from blues_lib.dp.executor.Executor import Executor

class HookProc(Executor):
  
  @abstractmethod
  def execute(self)->None:
    pass