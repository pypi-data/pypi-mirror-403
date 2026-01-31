from selenium.webdriver import ChromeService

class ServiceGetter:
  
  @classmethod
  def chrome(cls,executable_path:str='',port:int=0, log_path: str='')-> ChromeService:
    kwargs = {k: v for k, v in locals().items() if k != 'cls' and v}
    print(kwargs)
    return ChromeService(**kwargs)
