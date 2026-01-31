import logging
from abc import ABC,abstractmethod
from typing import Any

class Facade(ABC):

  def __init__(self):
    self._logger = logging.getLogger('airflow.task')
    # the mapping table: method name -> instance
    self._caller_instances:dict[str,Any] = {}
    self.register()

  @abstractmethod
  def register(self)->None:
    """
    register the caller instances
    Returns:
      dict: the mapping table: method name -> instance
    """
    pass

  @property
  def methods(self)->list[str]:
    return self._caller_instances.keys()

  def has(self,name:str)->bool:
    return name in self.methods

  def execute(self,name:str,*args,**kwargs)->Any:
    """
    invoke the method of the instance
    Args:
      name (str) : the method name
      args (tuple): the positional arguments
      kwargs (dict): the keyword arguments
    Returns:
      Any: the result of the method invocation
    """
    instance = self._caller_instances.get(name)
    if not instance:
      raise ValueError(f"method {name} not found")
    return getattr(instance,name)(*args,**kwargs)
