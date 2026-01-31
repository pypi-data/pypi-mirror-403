import sys,os,re

from blues_lib.sele.waiter.Querier import Querier 
from blues_lib.sele.action.Mouse import Mouse 

class Choice():
  
  def __init__(self,driver):
    self.__driver = driver
    self.__querier = Querier(driver,5)
    self.__mouse = Mouse(driver)

  def select(self,loc_or_elem,parent_loc_or_elem=None,timeout=5):
    '''
    Support multi input parameters as selectors
    Parameter:
      loc_or_elem {str|WebElemnt|list<str>|list<WebElement>} : one or a list of target element
      parent_loc_or_elem {str|WebElemnt} : the choicebox's parent element
    Returns:
      {int} : the selectd count
    '''
    count = 0
    if not loc_or_elem:
      return count

    loc_or_elems = loc_or_elem if type(loc_or_elem) == list else [loc_or_elem]
    for loc_or_elem in loc_or_elems:
      count += self.__toggle(loc_or_elem,True,parent_loc_or_elem,timeout)
    return count

  def deselect(self,loc_or_elem,parent_loc_or_elem=None,timeout=5):
    '''
    Support multi input parameters as selectors
    Parameter:
      loc_or_elem {str|WebElemnt|list<str>|list<WebElement>} : one or a list of target element
    Returns:
      {int} : the selectd count
    '''
    count = 0
    if not loc_or_elem:
      return count
    
    loc_or_elems = loc_or_elem if type(loc_or_elem) == list else [loc_or_elem]

    for loc_or_elem in loc_or_elems:
      count += self.__toggle(loc_or_elem,False,parent_loc_or_elem,timeout)
    return count

  def __toggle(self,loc_or_elem,checked=True,parent_loc_or_elem=None,timeout=5):
    '''
    Select the choice boxes by selectors
    Parameter
      loc_or_elem {str|WebElement} : boxes css selectors or WebElement
      - Maybe one element: 'iput[value=car]'
      - Maybe multi elements: 'input[value=car],input[value=boat]'
    Returns:
      {int} : selectd count
    '''
    count = 0
    web_elements = self.__querier.query_all(loc_or_elem,parent_loc_or_elem,timeout)
    if not web_elements:
      return count
    
    for web_element in web_elements:
      # select mode
      if checked and web_element.is_selected():
        continue
      # deselect mode
      if not checked and not web_element.is_selected():
        continue
      count+=1
      # use the action to roll in the element to viewport automatically
      self.__mouse.click(web_element)
    return count

  def is_selected(self,loc_or_elem,parent_loc_or_elem=None,timeout=5):
    web_element = self.__querier.query(loc_or_elem,parent_loc_or_elem,timeout)
    if not web_element:
      return False
    return web_element.is_selected()
