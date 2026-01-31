from functools import wraps
import logging

class ExceptionLog():
  def __init__(self):
    self._logger = logging.getLogger('airflow.task')

  def __call__(self,func):
    @wraps(func) 
    def wrapper(instance,*args,**kwargs):
      try:
        return func(instance,*args,**kwargs)
      except Exception as error:
        message:str = self._get_message(error)
        self._logger.error(f'{instance.__class__.__name__} : {message}')
        return None

    return wrapper
  
  def _get_message(self,error)->str:
    error_str = str(error)
    first_line:str = error_str.split('\n')[0].strip()
    if not first_line:
      first_line = error_str
    return first_line
