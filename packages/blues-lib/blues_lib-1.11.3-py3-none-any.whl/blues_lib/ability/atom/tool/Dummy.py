from typing import Any
from blues_lib.ability.atom.BaseAbility import BaseAbility
from blues_lib.types.common import AbilityOpts

class Dummy(BaseAbility):
  
  def dummy_info(self,options:AbilityOpts)->bool:
    self._logger.info(f'{self.__class__.__name__}: {options.get("value")}')
    return True

  def dummy_value(self,options:AbilityOpts)->Any:
    return options.get('value')
