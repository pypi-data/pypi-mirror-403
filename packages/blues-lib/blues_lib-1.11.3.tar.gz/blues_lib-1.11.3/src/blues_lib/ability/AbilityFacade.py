from blues_lib.ability.sequence.SeqAbilityDict import SeqAbilityDict
from blues_lib.ability.atom.AtomFacade import AtomFacade
from blues_lib.ability.atom.BaseAbility import BaseAbility

class AbilityFacade(AtomFacade):
  
  def _get_class_instances(self) -> dict[str,BaseAbility]:
    insts:dict[str,BaseAbility] = super()._get_class_instances()
    driver_insts = SeqAbilityDict.get(self._driver) or {}
    return {**insts,**driver_insts}
