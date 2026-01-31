import time,logging,json,requests
from blues_lib.types.llm import LLMMessage,LLMBaseReqOpts
from blues_lib.llm.DefaultLLMOpts import DefaultLLMOpts
from blues_lib.deco.ability.ValidateOptions import ValidateOptions

class BaseLLMClient:

  def __init__(self,req_opts:LLMBaseReqOpts) -> None:
    self._logger = logging.getLogger('airflow.task')
    self._prepare(req_opts)
    
  @ValidateOptions('llm_base_opts')
  def _prepare(self,req_opts:LLMBaseReqOpts):
    self._url = req_opts.get('url') or DefaultLLMOpts.URL

    payload = req_opts.get('payload') or {}
    default_payload = {**DefaultLLMOpts.PAYLOAD,**DefaultLLMOpts.DEEPSEEK_PAYLOAD} if self._is_deepseek_api() else DefaultLLMOpts.PAYLOAD
    self._payload = {**default_payload,**payload}

    headers = req_opts.get('headers') or {}
    self._headers = {**DefaultLLMOpts.HEADERS,**headers}
  
  def request(self,messages:list[LLMMessage]|None=None)->dict:
    if messages:
      self._payload['messages'] = messages
    payload = json.dumps(self._payload)
    try:
      self._console(self._payload['messages'])
      request_start = time.time()
      response = requests.request("POST", self._url, headers=self._headers, data=payload)
      request_end = time.time()

      if response.status_code != 200:
        raise Exception(f'LLM request error: {response.status_code} {response.text}')

      self._logger.info(f"LLM request time: {request_end - request_start:.2f} seconds")
      return response.json()
    except Exception as e:
      raise
    
  def _is_deepseek_api(self)->bool:
    return 'deepseek' in self._url.lower()

  def _console(self,messages:list[dict[str,str]]):
    url:str = self._url
    model:str = self._payload['model']
    self._logger.info(f'LLM : {url} {model}')

    if len(messages) < 2:
      system_content:str = ''
      user_content:str = messages[0]['content'].strip()
    else:
      system_content:str = messages[0]['content'].strip()
      user_content:str = messages[1]['content'].strip()

    if system_content:
      system_content_len = len(system_content)
      system_msg = system_content[:50]+'...' if system_content_len > 50 else system_content
      self._logger.info(f'LLM system prompt [{system_content_len}] : {system_msg}')

    user_content_len = len(user_content)
    user_msg = user_content[:50]+'...' if user_content_len > 50 else user_content
    self._logger.info(f'LLM user prompt [{user_content_len}] : {user_msg}')
    

