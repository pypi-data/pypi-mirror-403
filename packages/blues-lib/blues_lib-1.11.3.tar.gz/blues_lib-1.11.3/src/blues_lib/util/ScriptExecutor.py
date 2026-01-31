from typing import Any

class ScriptExecutor:

  @classmethod
  def execute(cls,script:str,input:Any|None=None)->Any:
    if not script:
      return input

    try:
      if script.strip().startswith("lambda"):
        return cls._execute_lambda(script,input)
      elif script.strip().startswith("def func"):
        return cls._execute_func(script,input)
      else:
        raise ValueError("脚本字符串仅支持lambda函数（以lambda开头）或多行函数（以def func开头）")
    except SyntaxError as e:
      raise SyntaxError(f"脚本语法错误：{e}\n错误脚本：{script}") from e
    except NameError as e:
      raise NameError(f"脚本引用未定义的变量/函数：{e}\n错误脚本：{script}") from e
    except Exception as e:
      raise Exception(f"脚本执行失败：{e}\n错误脚本：{script}") from e
    
  @classmethod
  def _execute_lambda(cls,script:str,input:Any|None=None)->Any:
    func = eval(script,globals={}, locals={})
    return func(input)

  @classmethod
  def _execute_func(cls,script:str,input:Any|None=None)->Any:
    local_ns = {}
    exec(script, globals={}, locals=local_ns)
    func = local_ns["func"]
    return func(input)
