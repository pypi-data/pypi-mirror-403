from typing import Any
from blues_lib.types.common import AbilityDef,SeqDef,AbilityDef,SeqDef,TaskDef
from blues_lib.ability.AbilityExecutor import AbilityExecutor
from blues_lib.task.BaseTask import BaseTask
from blues_lib.metastore.validate.MetaValidator import MetaValidator

class GenericTask(BaseTask):

  def _process(self,definition:TaskDef,bizdata:dict|None=None)->list[Any]|dict[str,Any]:
    validate_tpl = 'except.input.ability_def_col'
    abilities:list[AbilityDef|SeqDef]|dict[str,AbilityDef|SeqDef] = MetaValidator.validate_node_with_template('abilities',definition,validate_tpl)
    executor = AbilityExecutor()
    return executor.execute(abilities,bizdata)