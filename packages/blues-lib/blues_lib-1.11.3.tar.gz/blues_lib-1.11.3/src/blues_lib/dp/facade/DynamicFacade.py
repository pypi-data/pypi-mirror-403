from typing import Any
from abc import abstractmethod
from blues_lib.dp.facade.Facade import Facade

class DynamicFacade(Facade):
  
  def register(self) -> None:
    class_instances = self._get_class_instances()
    self._caller_instances = self._get_caller_instances(class_instances)
    
  @abstractmethod
  def _get_class_instances(self) -> dict[str,Any]:
    pass
  
  def _get_caller_instances(self,class_instances :dict[str,Any]) -> dict[str,Any]:
    """
    build a mapping table:
    Args:
      class_instances (dict[str,Any]): the mapping table: class name -> instance
    Returns:
      dict: the mapping table: method name -> instance
    """
    caller_instances = {**self._caller_instances}
    for class_name,instance in class_instances.items():
      # get instance all attr names
      attr_names:list[str] = dir(instance)
      for attr_name in attr_names:
        # skip the private attributes
        if attr_name.startswith("_"):
          continue
        # skip the attr which is not callable
        attr_obj = getattr(instance, attr_name)
        if not callable(attr_obj):
          continue
        # resolve method name conflict
        if attr_name in caller_instances:
          existing_instance = caller_instances[attr_name]
          message:str = f"{attr_name} exists in {type(existing_instance).__name__}, skip {class_name}"
          raise ValueError(message)
        # save to mapping table: method -> instance
        caller_instances[attr_name] = instance
    return caller_instances
