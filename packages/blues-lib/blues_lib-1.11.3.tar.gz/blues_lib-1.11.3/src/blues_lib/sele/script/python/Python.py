from blues_lib.util.ScriptExecutor import ScriptExecutor

class Python():
  
  def __init__(self,driver):
    self.driver = driver
  
  def execute(self,script:str):
    return ScriptExecutor.execute(script,self.driver)