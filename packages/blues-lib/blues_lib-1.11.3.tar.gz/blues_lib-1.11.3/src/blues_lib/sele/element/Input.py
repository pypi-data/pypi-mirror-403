import random,time
from selenium.webdriver.common.keys import Keys

from blues_lib.sele.waiter.Querier import Querier  

class Input():

  def __init__(self,driver):
    self.__driver = driver
    self.__querier = Querier(driver,5)

  def write(self,loc_or_elem,value,parent_loc_or_elem=None,timeout=5):
    '''
    Clear and write text into the text controller
    Parameter:
      loc_or_elem {str | WebElement} : the input element's css selecotr or web element
      texts {list<str>} : one or more text string
    '''
    web_element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)
    if not web_element:
      return None

    self.clear(web_element,None)

    self.append(web_element,value,None)

  def append(self,loc_or_elem,value,parent_loc_or_elem=None,timeout=5):
    '''
    Append text into the text controller
    Parameter:
      loc_or_elem {str | WebElement} : the input element's css selecotr or web element
      texts {list<str>} : one or more text string
    '''
    texts = value if type(value)==list else [value]

    web_element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)
    if not web_element:
      return None

    web_element.send_keys(*texts)

  def write_para(self,loc_or_elem,value,LF_count=1,parent_loc_or_elem=None,timeout=5):
    '''
    Write lines with line break
    Parameter:
      loc_or_elem {str | WebElement} : the input element's css selecotr or web element
      parent_loc_or_elem {str | WebElement} : the input element parent's css selecotr or web element
      texts {list<str>} : texts
      LF_count {int} : line break count in every para
      input_by_para {bool} : input txt para by para
    '''
    texts = value if type(value)==list else [value]
    paras = self.__get_paras(texts,LF_count)

    self.clear(loc_or_elem,parent_loc_or_elem,timeout)
    for para in paras:
      self.append(loc_or_elem,para,parent_loc_or_elem,timeout)

  def append_para(self,loc_or_elem,value,LF_count=1,parent_loc_or_elem=None,timeout=5):
    texts = value if type(value)==list else [value]
    paras = self.__get_paras(texts,LF_count)
    for para in paras:
      self.append(loc_or_elem,para,parent_loc_or_elem,timeout)

  def __get_paras(self,texts,LF_count):
    break_texts = []
    idx = 0
    max_idx = len(texts)-1
    for text in texts:
      break_texts.append(text)
      if idx<=max_idx:
        for i in range(LF_count):
          break_texts.append(Keys.ENTER)
      idx+=1
    return break_texts

  def write_discontinuous(self,loc_or_elem,value,parent_loc_or_elem=None,timeout=5,interval:list[int|float]|None=None):

    web_element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)
    if not web_element:
      return None

    self.clear(web_element,None)
    self.append_discontinuous(web_element,value,None,timeout,interval)
  
  def append_discontinuous(self,loc_or_elem,value,parent_loc_or_elem=None,timeout=5,interval:list[int|float]|None=None):

    '''
    Input chars non-uniform speed
    '''
    texts = value if type(value)==list else [value]
    web_element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)

    for text in texts:
      # input char by char
      for char in text:
        self.__input_discontinuous(web_element,char,interval)

  def __input_discontinuous(self,web_element,char,interval:list[int|float]|None=None):
    '''
    input the text one char by one char intermittently
    using a random interval
    '''
    if interval:
      time.sleep(random.uniform(interval[0],interval[1]))
    web_element.send_keys(char)

  def clear(self,loc_or_elem,parent_loc_or_elem=None,timeout=5):
    """
    清空元素内容，支持表单输入框和所有可编辑元素（含div、span等）
    """
    element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)
    tag_name = element.tag_name.lower()
    
    # 处理表单输入元素
    if tag_name in ['input', 'textarea']:
      element.clear()
    else:
      # 处理所有可编辑元素（不限制标签类型）
      contenteditable = element.get_attribute('contenteditable')
      # contenteditable可能为"true"或""（空字符串表示启用）
      is_editable = contenteditable in (True, 'true', '')
      if is_editable:
        self.__driver.execute_script("arguments[0].innerHTML = '';", element)