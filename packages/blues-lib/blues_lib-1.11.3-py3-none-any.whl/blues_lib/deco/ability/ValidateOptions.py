from functools import wraps
from blues_lib.metastore.validate.SchemaValidator import SchemaValidator
from blues_lib.types.common import AbilityOpts
import logging

class ValidateOptions():
  def __init__(self,tpl_name:str):
    self._logger = logging.getLogger('airflow.task')
    self._tpl_name = tpl_name

  def __call__(self,func):
    @wraps(func) 
    def wrapper(instance,*args,**kwargs):

      # options is optional
      if len(args)>0 and args[0]:
        options:AbilityOpts = args[0]
        tpl_path = f'except.input.{self._tpl_name}'
        stat,message = SchemaValidator.validate_with_template(options,tpl_path)
        if not stat:
          raise ValueError(message)

      return func(instance,*args,**kwargs)
    return wrapper