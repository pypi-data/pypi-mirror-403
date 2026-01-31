from selenium.webdriver.common.keys import Keys
from blues_lib.util.OSystem import OSystem

class OSKeys:
  
  _COMMON_KEYS = {
    "ctrl": Keys.CONTROL,
  }

  _MAC_KEYS = {
    "ctrl": Keys.COMMAND,
  }

  @classmethod
  def get(cls,key:str)->list[str]:
    if OSystem.get_os_type() == 'mac':
      return cls._MAC_KEYS.get(key,[])
    else:
      return cls._COMMON_KEYS.get(key,[])
