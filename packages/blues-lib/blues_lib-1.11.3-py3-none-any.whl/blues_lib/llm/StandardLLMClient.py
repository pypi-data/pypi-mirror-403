from blues_lib.types.llm import LLMMessage,LLMSTDReqOpts,LLMBaseReqOpts
from blues_lib.llm.BaseLLMClient import BaseLLMClient
from blues_lib.util.FileWriter import FileWriter
from blues_lib.deco.ability.ValidateOptions import ValidateOptions

class StandardLLMClient(BaseLLMClient):
  
  def __init__(self,std_opts:LLMSTDReqOpts) -> None:
    self._std_opts = std_opts
    base_opts:LLMBaseReqOpts = self._get_base_opts(std_opts)
    super().__init__(base_opts)
    
  def request(self,user_content:str|None=None,system_content:str|None=None)->str:
    messages:list[LLMMessage] = self._get_messages(user_content,system_content)
    chat_completion:dict = super().request(messages)
    content:str = self._get_content(chat_completion)
    save_path:str = self._std_opts.get('save_path','')
    return self._save_or_return(save_path,content)
    
  def _get_content(self,chat_completion:dict)->str:
    try:
      return chat_completion.get('choices',[{}])[0].get('message',{}).get('content','')
    except:
      self._logger.error(f'LLM output: no choices[0].message.content in {chat_completion}')
      return ''
    
  def _save_or_return(self,save_path:str,content:str)->str:
    if save_path:
      return FileWriter.write_text(save_path,content)
    else:
      return content
     
  @ValidateOptions('llm_std_opts')
  def _get_base_opts(self,std_opts:LLMSTDReqOpts)->LLMBaseReqOpts:
    url:str = std_opts.get('url','')
    api_key:str = std_opts.get('api_key','')
    
    payload:dict = self._get_payload(std_opts)
    headers:dict = {
      'Authorization': f'Bearer {api_key}',
    } if api_key else {}

    base_opts:LLMBaseReqOpts = {}
    if url:
      base_opts['url'] = url
    if payload:
      base_opts['payload'] = payload
    if headers:
      base_opts['headers'] = headers
    return base_opts

  @ValidateOptions('llm_std_opts')
  def _get_payload(self,std_opts:LLMSTDReqOpts) -> dict:
    model:str = std_opts.get('model','')
    system_content:str = std_opts.get('system_content','')
    user_content:str = std_opts.get('user_content','')

    payload:dict = {}
    if model:
      payload['model'] = model
    
    messages:list[LLMMessage] = self._get_messages(user_content,system_content)
    if messages:
      payload['messages'] = messages
    
    return payload

  def _get_messages(self,user_content:str|None=None,system_content:str|None=None)->list[LLMMessage]:
    max_prompt_length:int = int(self._std_opts.get('max_prompt_length',-1))
    messages:list[LLMMessage] = []
    if system_content:
      messages.append({
        "role": "system",
        "content": system_content,
      })
    if user_content:
      if max_prompt_length > 0 and len(user_content) > max_prompt_length:
        user_content = user_content[:max_prompt_length]
      messages.append({
        "role": "user",
        "content": user_content,
      })
    return messages