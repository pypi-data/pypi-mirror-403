import logging
from typing import Callable
from blues_lib.util.NestedDataMapping import NestedDataMapping
from blues_lib.types.common import InputMapping

class XComMapper:

  def __init__(self,mappings:list[InputMapping],bizdata:dict,ti:any) -> None:
    self._mappings = mappings
    self._bizdata = bizdata
    self._ti = ti
    self._logger = logging.getLogger('airflow.task')

  def handle(self):
    for mapping in self._mappings:
      source:str = mapping.get('source')
      target:str = mapping.get('target')
      callback:Callable = mapping.get('callback')
      if not source:
        continue
      if not target:
        target='bizdata'
      self._map(source,target,callback)
      
  def _map(self,source:str,target:str,callback:Callable):

    message:str = f'{source} -> {target}' 
    source_data,source_attr_chain = self._get_source_data(source)
    if not source_data:
      self._logger.warning(f'{self.__class__.__name__} Failed to map: {message} because source data is empty')
      return
    
    target_data,target_attr_chain = self._get_target_data(target)
    # allow empty list or dict as target
    if target_data is None:
      self._logger.warning(f'{self.__class__.__name__} Failed to map: {message} because target data is None')
      return

    has_mapped = NestedDataMapping.map(source_data,source_attr_chain,target_data,target_attr_chain,callback) 
    if not has_mapped:
      raise Exception(f'Failed to map: {message}')
    else:
      source_data_str = str(source_data)
      source_data_str = source_data_str if len(source_data_str) < 50 else source_data_str[:50]+'...'
      self._logger.info(f'{self.__class__.__name__} Managed to map: {message} ; source_data: {source_data_str}')
      
  def _get_target_data(self,target:str)->tuple[any,str]:
    target_slices:list[str] = target.split('/')
    if len(target_slices) < 1:
      return None,''
    
    target_root:str = target_slices[0]
    attr_chain:str = target_slices[1] if len(target_slices) > 1 else ''
    
    if target_root !='bizdata':
      return None,attr_chain

    bizdata = self._bizdata
    return bizdata,attr_chain
    
  def _get_source_data(self,source:str)->tuple[any,str]:
    source_slices:list[str] = source.split('/')
    if len(source_slices) < 2:
      return None,''
    
    task_id:str = source_slices[0]
    key:str = source_slices[1]
    attr_chain:str = source_slices[2] if len(source_slices) > 2 else ''
    source_root_data:any = self._ti.xcom_pull(task_ids=task_id,key=key)
    if not source_root_data:
      return None,attr_chain 
    
    return source_root_data,attr_chain
