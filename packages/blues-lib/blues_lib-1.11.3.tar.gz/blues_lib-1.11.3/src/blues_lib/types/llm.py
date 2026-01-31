
from typing import TypeAlias,TypedDict,Literal

LLMRole: TypeAlias = Literal["system","user","assistant"]

LLMMessage: TypeAlias = TypedDict("LLMMessage", {
  "role": LLMRole,
  "content": str,
})

LLMBaseReqOpts: TypeAlias = TypedDict("LLMBaseReqOpts", {
  "url":str,
  "payload":dict,
  "headers":dict, 
})

LLMSTDReqOpts: TypeAlias = TypedDict("LLMSTDReqOpts", {
  "url":str,
  "api_key":str,
  "model":str,
  "system_content":str,
  "user_content":str,
  
  "max_prompt_length":int,
  "save_path":str,
})