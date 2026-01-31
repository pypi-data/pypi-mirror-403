from blues_lib.ability.atom.BaseAbility import BaseAbility
from blues_lib.llm.BaseLLMClient import BaseLLMClient
from blues_lib.llm.StandardLLMClient import StandardLLMClient
from blues_lib.llm.JSONLLMClient import JSONLLMClient
from blues_lib.types.common import AbilityOpts
from blues_lib.types.llm import LLMBaseReqOpts,LLMSTDReqOpts

class LLMClient(BaseAbility):
  
  def base_llm_request(self,options:AbilityOpts)->dict:
    requet_opts:LLMBaseReqOpts = options.get('value')
    client = BaseLLMClient(requet_opts)
    return client.request()

  def standard_llm_request(self,options:AbilityOpts)->str:
    requet_opts:LLMSTDReqOpts = options.get('value')
    client = StandardLLMClient(requet_opts)
    return client.request()
  
  def json_llm_request(self,options:AbilityOpts)->list|dict:
    requet_opts:LLMSTDReqOpts = options.get('value')
    client = JSONLLMClient(requet_opts)
    return client.request()