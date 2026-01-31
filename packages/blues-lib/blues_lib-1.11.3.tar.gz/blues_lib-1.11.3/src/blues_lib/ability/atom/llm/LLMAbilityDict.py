from blues_lib.ability.atom.llm.LLMClient import LLMClient

class LLMAbilityDict():

  @classmethod
  def get(cls)->dict:
    return {
      LLMClient.__name__:LLMClient(),
    }