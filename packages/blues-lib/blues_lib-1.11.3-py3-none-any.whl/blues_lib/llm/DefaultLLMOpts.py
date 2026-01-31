import os
class DefaultLLMOpts:

  URL = os.environ.get("LLM_API_URL","") or "https://api.deepseek.com/chat/completions"
  
  PAYLOAD = {
    "messages": [
      {
        "content": "You are a helpful assistant",
        "role": "system"
      },
      {
        "content": "Hi",
        "role": "user"
      }
    ],
    "model": os.environ.get("LLM_API_MODEL","") or "deepseek-chat",
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stream": False,
    "temperature": 1,
    "top_p": 1,
  }
  
  DEEPSEEK_PAYLOAD = {
    "response_format": {
      "type": "text"
    },
    "stop": None,
    "max_tokens": 8000, # max 8192
    "thinking": {
      "type": "disabled"
    },
    "stream_options": None,
    "tools": None,
    "tool_choice": "none",
    "logprobs": False,
    "top_logprobs": None
  }

  HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {os.environ.get("LLM_API_KEY","")}'
  }