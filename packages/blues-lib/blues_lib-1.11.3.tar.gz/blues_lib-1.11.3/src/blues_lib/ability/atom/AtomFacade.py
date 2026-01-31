from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.dp.facade.DynamicFacade import DynamicFacade
from blues_lib.ability.atom.BaseAbility import BaseAbility

from blues_lib.ability.atom.webdriver.DriverAbilityDict import DriverAbilityDict
from blues_lib.ability.atom.matcher.MatcherAbilityDict import MatcherAbilityDict
from blues_lib.ability.atom.tool.ToolAbilityDict import ToolAbilityDict
from blues_lib.ability.atom.llm.LLMAbilityDict import LLMAbilityDict

class AtomFacade(DynamicFacade):
  
  def __init__(self,driver:WebDriver|None = None) -> None:
    self._driver = driver
    super().__init__()
    
  def _get_class_instances(self) -> dict[str,BaseAbility]:
    undriver_insts = {
      **ToolAbilityDict.get(),
      **LLMAbilityDict.get(),
    }
    driver_insts = {
      **DriverAbilityDict.get(self._driver),
      **MatcherAbilityDict.get(self._driver),
    } if self._driver else {}
    return {**undriver_insts,**driver_insts}
