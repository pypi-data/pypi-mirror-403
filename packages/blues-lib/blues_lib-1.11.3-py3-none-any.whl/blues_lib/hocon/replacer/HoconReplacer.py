from blues_lib.hocon.replacer.Replacer import Replacer  
from blues_lib.hocon.replacer.IncludeReplacer import IncludeReplacer
from blues_lib.hocon.replacer.FunctionReplacer import FunctionReplacer
from blues_lib.hocon.replacer.EnvReplacer import EnvReplacer
from blues_lib.hocon.replacer.VariableReplacer import VariableReplacer

class HoconReplacer(Replacer):
  
  def replace(self)->dict:
    # return a deep clone of the template
    template:dict = self._template
    variables:dict = self._variables
    config:dict = self._config

    # chains
    template:dict = IncludeReplacer(template).replace()
    template:dict = FunctionReplacer(template).replace()
    template:dict = EnvReplacer(template).replace()
    template:dict = VariableReplacer(template,variables,config).replace()
    return template
  
  def replace_with_env(self):
    return EnvReplacer(self._template).replace()
  
  def replace_with_include(self):
    return IncludeReplacer(self._template).replace()
  
  def replace_with_function(self):
    return FunctionReplacer(self._template).replace()
  
  def replace_with_variable(self):
    return VariableReplacer(self._template,self._variables,self._config).replace()
  