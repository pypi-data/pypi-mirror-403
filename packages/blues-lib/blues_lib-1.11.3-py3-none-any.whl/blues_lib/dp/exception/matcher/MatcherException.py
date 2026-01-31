from typing import Any
from blues_lib.types.common import AbilityCondition

class MatcherException(Exception):
  # 自定义异常：matcher 匹配失败
  def __init__(self, matcher:str,matched:bool,value:Any,expected:Any,condition:AbilityCondition):
    message:str = "Matched" if matched else "Unmatched"
    message+= f' [{matcher}] '
    expression:str = f'"{value}"=="{expected}"' if matched else f'"{value}"!="{expected}"'
    message+=expression
    message = f'{self.__class__.__name__} {message} {condition}'
    super().__init__(message)