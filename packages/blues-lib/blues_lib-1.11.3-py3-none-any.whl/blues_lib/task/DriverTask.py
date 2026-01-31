from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.types.common import TaskDef,DriverDef
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.task.BaseTask import BaseTask
from blues_lib.task.driver.DriverInitializer import DriverInitializer

class DriverTask(BaseTask):

  def _prepare(self,definition:TaskDef,bizdata:dict|None=None)->None:
    self._driver_def:DriverDef = MetaRenderer.render_node('driver',definition,bizdata)
    self._driver = DriverInitializer(self._driver_def,bizdata).init()

  def _process(self,definition:TaskDef,bizdata:dict|None=None)->list[Any]|dict[str,Any]:
    # Create the driver, and login if needed and store it in context
    self._prepare(definition,bizdata)

    key:str = 'driver'
    if not self._driver or not isinstance(self._driver,WebDriver):
      raise ValueError(f"{self.__class__.__name__} failed to create the driver")

    if self._context is None:
      raise ValueError(f"{self.__class__.__name__} context is required for DriverTask")

    if self._context.get(key):
      self._context[key].quit()
    self._context[key] = self._driver

    return {
      'data':{
        'key':key,
      },
      'success':True,
    }
      