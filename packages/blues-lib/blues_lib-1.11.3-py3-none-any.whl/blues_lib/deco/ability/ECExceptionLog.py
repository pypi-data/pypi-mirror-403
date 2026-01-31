import inspect
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from functools import wraps
import logging
from blues_lib.types.common import AbilityOpts

class ECExceptionLog():
  def __init__(self,error:str=''):
    self._logger = logging.getLogger('airflow.task')
    self._error = error

  def __call__(self,func):
    @wraps(func) 
    def wrapper(instance,*args,**kwargs):
      try:
        return func(instance,*args,**kwargs)
      except Exception as error:
        options:AbilityOpts = args[1]
        print(options)
        message:str = self._get_message(options)
        self._logger.error(f'{instance.__class__.__name__} : {message}')
        return None

    return wrapper
  
  def _get_message(self,options:AbilityOpts)->str:
    stack_list = inspect.stack()
    caller_stack = stack_list[2]
    caller_name = caller_stack[3]
    
    options = options or {}
    opts_message:str = ''
    for key,value in options.items():
      if not value:
        continue
      if isinstance(value,WebDriver):
        value='WebDriver'
      elif isinstance(value,WebElement):
        value='WebElement'
      opts_message += f'{key}="{value}", '

    return f'Unmatches the condition {caller_name} by {opts_message}'
