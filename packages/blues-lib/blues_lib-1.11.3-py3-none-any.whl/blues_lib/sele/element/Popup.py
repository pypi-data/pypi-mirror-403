import sys,os,re

from blues_lib.sele.element.Finder import Finder 
from blues_lib.sele.element.State import State 
from blues_lib.sele.interactor.Frame import Frame 
from blues_lib.sele.script.javascript.JavaScript import JavaScript 

class Popup():
  '''
  Handle automatic pop-up AD boxes
  '''
  def __init__(self,driver):
    self.__driver = driver
    self.__finder = Finder(driver)
    self.__state = State(driver)
    self.__frame = Frame(driver)
    self.__javascript = JavaScript(driver)

  def remove(self,loc_or_elem):
    '''
    Remove the popup elements
    Parameter:
      loc_or_elem {list<str>} : target_CSs selector list
    Returns:
      {int} : removed count
    '''
    count = 0
    if not loc_or_elem:
      return count
    
    loc_or_elems = loc_or_elem if type(loc_or_elem) == list else [loc_or_elem]

    for CS_WE in loc_or_elems:
      count += self.__javascript.remove(CS_WE)

    return count

  def close(self,loc_or_elem,parent_loc_or_elem=None,frame_loc_or_elem=None):
    '''
    Close one or multi popups
    Parameter:
      off_locators { list<[close_CS_WE,frame_loc_or_elem]> | list<close_CS_WE>} 
    Returns:
      {int} : the closed count
    '''
    count = 0
    if not loc_or_elem:
      return count

    loc_or_elems = loc_or_elem if type(loc_or_elem)==list else [loc_or_elem]
    
    for CS_WE in loc_or_elems:
      count += self.__close(CS_WE,parent_loc_or_elem,frame_loc_or_elem)

    return count

  def __close(self,close_CS_WE,parent_loc_or_elem=None,frame_loc_or_elem=None):
    count = 0
    # switch to frame
    if frame_loc_or_elem:
      self.__frame.switch_to(frame_loc_or_elem)      

    web_elements = self.__finder.find_all(close_CS_WE,parent_loc_or_elem)
    if not web_elements:
      # switch back
      if frame_loc_or_elem:
        self.__frame.switch_to_default()      

      return count
    
    for web_element in web_elements:
      if self.__state.is_displayed(web_element):
        count+=1
        self.__mouse.click(web_element)
    
    # switch back
    if frame_loc_or_elem:
      self.__frame.switch_to_default()      

    return count


