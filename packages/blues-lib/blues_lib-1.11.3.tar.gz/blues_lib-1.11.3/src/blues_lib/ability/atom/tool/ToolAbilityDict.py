from blues_lib.ability.atom.tool.Dummy import Dummy
from blues_lib.ability.atom.tool.Util import Util

class ToolAbilityDict():

  @classmethod
  def get(cls)->dict:
    return {
      Dummy.__name__:Dummy(),
      Util.__name__:Util(),
    }