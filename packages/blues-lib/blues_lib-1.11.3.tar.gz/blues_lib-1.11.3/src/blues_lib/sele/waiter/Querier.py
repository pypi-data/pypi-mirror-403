from selenium.webdriver.remote.webelement import WebElement
from blues_lib.sele.waiter.EC import EC   
from blues_lib.sele.waiter.deco.QuerierDeco import QuerierDeco
from blues_lib.sele.element.Finder import Finder   

# 提供元素选择功能
class Querier():

  def __init__(self,driver,timeout=8):
    self.__driver = driver
    self.__ec = EC(driver) 
    self.__finder = Finder(driver) 
    self.__timeout = timeout or 5

  def setTimeout(self,timeout=5):
    '''
    Adjust the timeout in runtime
    '''
    self.__timeout = timeout

  @QuerierDeco('query')
  def query(self,loc_or_elem,parent_loc_or_elem=None,timeout=5)->WebElement|None:
    '''
    Wait and get the element from document or parent element
    Parameter:
      loc_or_elem {str|WebElement} : the target element's css selector or WebElement
      parent_loc_or_elem {str|WebElement} : the parent element's css selector or WebElement
      timeout {int} : Maximum waiting time (s)
    Returns:
      {WebElement|None} 
    '''
    if not loc_or_elem:
      return None
    if not parent_loc_or_elem:
      return self.__query(loc_or_elem,timeout)

    parent:WebElement|None = self.__query(parent_loc_or_elem,timeout) 
    if parent:
      return self.__finder.find(loc_or_elem,parent)
    else:
      return self.__query(loc_or_elem,timeout)

  @QuerierDeco('query_all')
  def query_all(self,loc_or_elem,parent_loc_or_elem=None,timeout=5)->list[WebElement]|None:
    '''
    Wait and get elements from document or parent element
    Parameter:
      loc_or_elem {str|WebElement} : the target element's css selector or WebElement
      parent_loc_or_elem {str|WebElement} : the parent element's css selector or WebElement
      timeout {int} : Maximum waiting time (s)
    Returns:
      {list<WebElement>} 
    '''
    if not loc_or_elem:
      return None
    
    if not parent_loc_or_elem:
      return self.__query_all(loc_or_elem,timeout)

    parent:WebElement|None = self.__query(parent_loc_or_elem,timeout)
    if parent:
      return self.__finder.find_all(loc_or_elem,parent)
    else:
      return self.__query_all(loc_or_elem,timeout)

  def __query(self,loc_or_elem,timeout=5,parent_loc_or_elem=None)->WebElement|None:
    '''
    Wait and Get the target WebElement
    Parameter:
      loc_or_elem {str|WebElement} : the target element's css selector or WebElement
      timeout {int} : Maximum waiting time (s)
    Returns:
      {WebElement|None} 
    '''
    if isinstance(loc_or_elem,WebElement):
      return loc_or_elem
    
    wait_time = timeout or self.__timeout
    return self.__ec.to_be_presence(loc_or_elem,wait_time,parent_loc_or_elem)

  def __query_all(self,loc_or_elem,timeout=5,parent_loc_or_elem=None)->list[WebElement]|None:
    '''
    Wait and Get the target WebElements
    Parameter:
      loc_or_elem {str|WebElement} : css selector or web element
      timeout {int} : Maximum waiting time (s)
    Returns:
      {list<WebElement>} 
    '''
    if isinstance(loc_or_elem,WebElement):
      return [loc_or_elem]

    wait_time = timeout or self.__timeout
    return self.__ec.all_to_be_presence(loc_or_elem,wait_time,parent_loc_or_elem)

   
