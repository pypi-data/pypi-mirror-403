from typing import Union
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.shadowroot import ShadowRoot
from blues_lib.sele.element.Locator import Locator  
from selenium.webdriver.support.relative_locator import locate_with
from .deco.FinderDeco import FinderDeco   

# 联合类型：直接包含所有支持元素查找的具体类型（适用于不需要泛型的场景）
SearchContext = Union[WebDriver, WebElement, ShadowRoot]

class Finder():
  def __init__(self,driver):
    self._driver = driver
  
  # === part 1:  geneal === #
  @FinderDeco('find')
  def find(self,loc_or_elem,parent_loc_or_elem=None)->WebElement|None:
    '''
    Get the first element in the DOM that matches with the provided locator.
    Parameter:
      loc_or_elem {str|WebElement} : the target element's css selector or WebElement - element_or_selector
      parent_loc_or_elem {str|WebElement} : the parent element's css selector or WebElement - element_or_selector
        - By default: the parent is the driver (the entire DOM)
    @returns {WebElement|None}
    '''
    if not loc_or_elem:
      return None

    if isinstance(loc_or_elem,WebElement):
      return loc_or_elem

    context: SearchContext = self.get_context(parent_loc_or_elem)
    return self._find(loc_or_elem,context)

  @FinderDeco('find_all')
  def find_all(self,loc_or_elem,parent_loc_or_elem=None)->list[WebElement]|None:
    '''
    Get all elements in the DOM that matches with the provided locator.
    loc_or_elem {str|WebElement} : the target element's css selector or WebElement
    parent_loc_or_elem {str|WebElement} : the parent element's css selector or WebElement
      - By default: the parent is the driver {WEbDriver} (the entire DOM)
    @returns {list<WebElement>}
    '''
    if not loc_or_elem:
      return None
    
    if isinstance(loc_or_elem,WebElement):
      return [loc_or_elem]
    
    context: SearchContext = self.get_context(parent_loc_or_elem)
    return self._find_all(loc_or_elem,context)

  # === part 2:  get shadow element === #
  @FinderDeco('find_shadow')
  def find_shadow(self,loc_or_elem,parent_loc_or_elem)->WebElement|None:
    '''
    Find the element in shadow root
    Parameter:
      loc_or_elem {str} : css selector of the element in the shadow root
      parent_loc_or_elem {str|WebElement} : the element contains the shadow root
    '''
    if not loc_or_elem:
      return None
    
    context: SearchContext|None = self._get_shadow_context(parent_loc_or_elem)
    if not context:
      return None

    return self._find(loc_or_elem,context)

  @FinderDeco('find_all_shadow')
  def find_all_shadow(self,loc_or_elem,parent_loc_or_elem)->list[WebElement]|None:
    '''
    Find all elements in shadow root
    Parameter:
      loc_or_elem {str} : css selector of the element in the shadow root
      parent_loc_or_elem {str|WebElement} : the element contains the shadow root
    '''
    if not loc_or_elem:
      return None
    
    context: SearchContext|None = self._get_shadow_context(parent_loc_or_elem)
    if not context:
      return None

    return self._find_all(loc_or_elem,context)

  # === part 4:  get element by other element postion === #
  @FinderDeco('find_above')
  def find_above(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->WebElement|None:
    '''
    Find the target element above the anchor element
    - 目标元素的底部边缘必须位于锚点元素的顶部边缘之上（即目标元素整体在锚点元素的正上方或斜上方）。
    - 无论目标元素和锚点元素在 HTML 结构中是否为父子关系、兄弟关系，只要视觉上满足 “目标在锚点上方”，就能被匹配。
    - 如果存在多个符合 “在锚点上方” 条件的元素，above() 会优先返回与锚点元素水平重叠最多的那个（即最 “正上方” 的元素）。
    - 只要目标元素底部边缘在锚点元素顶部边缘之上（无论两者垂直距离多远，哪怕间隔整个屏幕），都符合 above() 条件。
    Parameter:
      target_CS {str} : the target element's selector, general is a tag selector
      anchor_CS {str} : the anchor element's selector
    Returns:
      {WebElement]
    '''
    return self.find_relative('above',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_above_all(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative_all('above',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_below(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->WebElement|None:
    return self.find_relative('below',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_below_all(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative_all('below',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_left(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->WebElement|None:
    return self.find_relative('left',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_left_all(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative_all('left',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_right(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative('right',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_right_all(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative_all('right',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_near(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    # you can use the near method to identify an element that is at most 50px away from the provided locator
    return self.find_relative('near',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_near_all(self,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    return self.find_relative_all('near',loc_or_elem,anchor_CS_WE,parent_loc_or_elem)

  def find_relative(self,position:str,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->WebElement|None:
    if not loc_or_elem or not anchor_CS_WE:
      return None

    locator = self._get_relative_locator(position,loc_or_elem,anchor_CS_WE)
    context = self.get_context(parent_loc_or_elem)
    return context.find_element(locator)

  def find_relative_all(self,position:str,loc_or_elem,anchor_CS_WE,parent_loc_or_elem=None)->list[WebElement]|None:
    if not loc_or_elem or not anchor_CS_WE:
      return None
    
    locator = self._get_relative_locator(position,loc_or_elem,anchor_CS_WE)
    context = self.get_context(parent_loc_or_elem)
    return context.find_elements(locator)

  # === appendix:  private methods === #
  def _get_relative_locator(self,position:str,loc_or_elem,anchor_CS_WE):
    target_locator:list[str] = Locator.get(loc_or_elem)
    anchor_ele = self.find(anchor_CS_WE)
    if not anchor_ele:
      return None

    if position == 'above':
      return locate_with(*target_locator).above(anchor_ele)
    elif position == 'below':
      return locate_with(*target_locator).below(anchor_ele)
    elif position == 'left':
      return locate_with(*target_locator).to_left_of(anchor_ele)
    elif position == 'right':
      return locate_with(*target_locator).to_right_of(anchor_ele)
    elif position == 'near':
      return locate_with(*target_locator).near(anchor_ele)
    
  def get_parent(self,parent_loc_or_elem)->WebElement|None:
    if not parent_loc_or_elem:
      return None

    # can't use type or undetected_chromedriver can not match
    if isinstance(parent_loc_or_elem,WebElement):
      return parent_loc_or_elem

    return self._find(parent_loc_or_elem,self._driver)
  
  def get_context(self,parent_loc_or_elem)->SearchContext:
    parent: WebElement|None = self.get_parent(parent_loc_or_elem)
    return parent or self._driver

  def _get_shadow_context(self,parent_loc_or_elem)->SearchContext|None:
    parent: WebElement|None = self.get_parent(parent_loc_or_elem)
    return parent.shadow_root if parent else None

  def _find(self,loc_or_elem:str,context:SearchContext)->WebElement|None:
    try:
      locator = Locator.get(loc_or_elem)
      return context.find_element(*locator)
    except Exception as e:
      return None

  def _find_all(self,loc_or_elem:str,context:SearchContext)->list[WebElement]|None:
    locator = Locator.get(loc_or_elem)
    return context.find_elements(*locator) or None
