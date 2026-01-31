from selenium.webdriver.remote.webelement import WebElement
from blues_lib.sele.browser.Browser import Browser 

class CrawlAsserter:
  def __init__(self,browser:Browser,condition:list) -> None:
    self._browser = browser
    self._condition = condition
    
  def expect(self)->bool:
    if len(self._condition)<2:
      return True
    
    loc_or_elem = self._condition[0]
    method = self._condition[1]
    value = None
    if len(self._condition)>2:
      value = self._condition[2]

    func = getattr(self, method, None)
    # 2. 校验方法是否存在且是可调用的函数
    if func and callable(func):
      ele:WebElement = self._browser.waiter.querier.query(loc_or_elem,timeout=1)
      # 3. 调用方法并传递参数
      return func(ele,value)
    else:
      return False
  
  def to_be_truthy(self,ele:WebElement,value)->bool:
    return bool(ele)

  def to_be_falsy(self,ele:WebElement,value)->bool:
    return not bool(ele)
