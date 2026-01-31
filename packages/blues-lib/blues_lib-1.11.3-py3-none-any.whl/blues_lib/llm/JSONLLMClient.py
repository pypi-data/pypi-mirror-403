import json
from blues_lib.llm.StandardLLMClient import StandardLLMClient
from blues_lib.types.llm import LLMSTDReqOpts
from blues_lib.util.FileWriter import FileWriter

class JSONLLMClient(StandardLLMClient):

  def __init__(self,std_opts:LLMSTDReqOpts) -> None:
    super().__init__(std_opts)
    self._set_response_format()
    
  def _set_response_format(self):
    if self._payload.get('response_format'):
      self._payload['response_format']['type'] = 'json_object'
    
  def _save_or_return(self,save_path:str,content:str)->str|list|dict:
    json_content:list|dict = self._parse_json(content)
    if save_path:
      return FileWriter.write_json(save_path,json_content)
    else:
      return json_content
    
  def _parse_json(self,content:str)->list|dict:
    try:
      return json.loads(content)
    except:
      self._logger.error(f'LLM output: invalid json str "{content}"')
      return {}
    
  def _validate_json_prompt(self,user_content:str|None=None,system_content:str|None=None)->bool:
    default_u_content:str = ''
    default_s_content:str = ''
    messages:list[dict[str,str]] = self._payload['messages']
    if len(messages) < 2:
      default_u_content = messages[0]['content'].strip()
    else:
      default_s_content = messages[0]['content'].strip()
      default_u_content = messages[1]['content'].strip()

    s_content:str = system_content or default_s_content
    u_content:str = user_content or default_u_content
    if 'json' not in u_content.lower() and 'json' not in s_content.lower():
      raise ValueError('LLM prompt: no json keyword in user_content and system_content')
    