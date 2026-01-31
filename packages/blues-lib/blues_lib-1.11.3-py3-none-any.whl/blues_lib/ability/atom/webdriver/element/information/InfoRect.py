from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.element.information.InfoBase import InfoBase
from blues_lib.types.common import AbilityOpts

class InfoRect(InfoBase):   
  """
  Information class to get element rectangle information.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/information/#rect
  """

  def get_rect(self,options:AbilityOpts)->dict[str,int]|None:
    '''
    Fetching element's size and position, this postiion:
    - 相对于当前可见视口（Viewport）
    - 相对坐标（视口相对坐标）
    - 页面滚动后，视口位置改变，该坐标会同步变化
    - 元素左上角在「当前可见窗口」中的位置
    Args:           
      options (AbilityOpts) : the element query options
    Returns:
      dict[str,int] : the element's width, height, x and y
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.rect if elem else None

  def get_size(self,options:AbilityOpts)->dict[str,int]|None:
    '''
    Fetching element's size
    Args:           
      options (AbilityOpts) : the element query options
    Returns:
      dict[str,int] : the element's width and height
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.size if elem else None

  def get_location(self,options:AbilityOpts)->dict[str,int]|None:
    '''
    Fetching element's location by the document
    - 相对于整个页面文档（Document）的左上角
    - 绝对坐标（页面绝对坐标）
    - 元素在页面中的绝对位置固定，不受滚动影响
    - 元素左上角在「整个页面」中的固定位置
    Args:           
      options (AbilityOpts) : the element query options
    Returns:
      dict[str,int] : the element's x and y
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.location if elem else None

