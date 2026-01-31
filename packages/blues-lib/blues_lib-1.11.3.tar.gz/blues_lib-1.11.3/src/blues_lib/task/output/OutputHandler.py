from typing import Any
from blues_lib.dp.output.STDOut import STDOut

class OutputHandler:

  @classmethod
  def push_to_xcom(cls,ti:any,results:list[Any]|dict[str,Any])->None:
    stdout:STDOut = cls._resolve(results)

    result = stdout.to_dict()
    for key,value in result.items():
      ti.xcom_push(key,value)

  @classmethod
  def _resolve(cls,results:list[Any]|dict[str,Any])->STDOut:
    if isinstance(results,list):
      return STDOut(200,'ok',results)
    elif isinstance(results,dict):
      return cls._get_dict_stdout(results)
     
  @classmethod
  def _get_dict_stdout(cls,results:dict[str,Any])->STDOut:
      data:list[Any]|dict[str,Any] = results if 'data' not in results else results.get('data')
      code:int = 200 if ('success' not in results or results.get('success')) else 500
      message:str = 'ok' if code==200 else 'not match'
      return STDOut(code,message,data)
 