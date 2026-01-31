from typing import Any
from blues_lib.util.NestedDataReader import NestedDataReader
from blues_lib.util.NestedDataWriter import NestedDataWriter
from blues_lib.util.NestedDataUpdater import NestedDataUpdater
from blues_lib.util.ScriptExecutor import ScriptExecutor

class NestedDataMapping:
  """嵌套数据映射类，用于在源数据和目标数据之间进行基于路径的映射"""
  @classmethod
  def map(cls,source_data: Any, source_path: str, target_data: Any, target_path: str, callback:str='') -> bool:
    """
    将源数据中指定路径的值映射到目标数据的指定路径
    参数: 源数据、源路径、目标数据、目标路径、映射前lambda函数(将源数据转换后再进行映射)
    返回: 映射是否成功
    """
    # 从源数据读取值
    value = NestedDataReader.read_by_path(source_data,source_path)
    value = ScriptExecutor.execute(callback,value) if callback else value

    # 替换目标数据中的值
    return NestedDataWriter.write_by_path(target_data,target_path,value)

  @classmethod
  def update(cls,source_data: Any, source_path: str, target_data: Any, target_path: str, callback:str='') -> bool:
    """
    将源数据中指定路径的值映射到目标数据的指定路径
    参数: 源数据、源路径、目标数据、目标路径、映射前lambda函数(将源数据转换后再进行映射)
    返回: 映射是否成功
    """
    # 从源数据读取值
    value = NestedDataReader.read_by_path(source_data,source_path)
    value = ScriptExecutor.execute(callback,value) if callback else value

    # 合并到目标dict
    return NestedDataUpdater.write_by_path(target_data,target_path,value)
