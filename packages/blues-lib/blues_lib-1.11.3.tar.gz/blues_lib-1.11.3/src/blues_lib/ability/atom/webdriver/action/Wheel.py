from blues_lib.ability.atom.webdriver.wait.Querier import Querier
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility

class Wheel(DriverAbility):
  '''
  A representation of a scroll wheel input device for interacting with a web page.
  Reference : https://www.selenium.dev/documentation/webdriver/actions_api/wheel/
  '''

  def __init__(self,driver):
    super().__init__(driver)
    self._querier = Querier(driver)
    self._chains = ActionChains(driver)

  def scroll_to_element(self,options:AbilityOpts)->bool:
    '''
    The actions class does not automatically scroll the target element into view,
    So this method will need to be used if elements are not already inside the viewport.
    The viewport will be scrolled so the bottom of the element is at the bottom of the screen.
    
    Args:
      options (AbilityOpts): The element query options
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False
    self._chains.scroll_to_element(elem).perform()
    return True

  def scroll_by_amount(self,options:AbilityOpts)->bool:
    '''
    Scroll by given amount
    This is the second most common scenario for scrolling. 
    Pass in an delta x and a delta y value for how much to scroll in the right and down directions. 
    Negative values represent left and up, respectively.
    Args:
      options (AbilityOpts): The scroll amount in the x and y directions.
    Returns:
      bool
    '''
    value:tuple[int,int] = options.get('value')
    self._chains.scroll_by_amount(*value).perform()
    return True
    
  def scroll_to_viewport(self,options:AbilityOpts)->bool:
    '''
    Scroll the element's center to the center of the viewport
    Args:
      options (AbilityOpts): The element query options
    Returns:
      bool: True if scroll success, False if element not found.
    '''
    elem: WebElement | None = self._querier.query_element(options)
    if not elem:
      return False
    
    # replace the target, avoid to research
    options['target'] = elem

    # 步骤1：获取窗口（视口）尺寸和窗口中心（视口内相对坐标）
    window_size = self._driver.get_window_size()
    viewport_center_x = window_size['width'] // 2
    viewport_center_y = window_size['height'] // 2

    # 步骤2：获取元素的关键坐标（修复核心：获取绝对坐标 + 正确计算元素中心）
    # 2.1 获取元素相对于页面文档的绝对坐标（x/y 是元素左上角的页面绝对位置）
    # 替代 elem.rect.x/elem.rect.y，避免视口相对坐标的偏差
    element_abs_x = elem.location['x']
    element_abs_y = elem.location['y']

    # 2.2 获取元素自身尺寸
    element_width = elem.size['width']
    element_height = elem.size['height']

    # 2.3 计算「元素中心的页面绝对坐标」（核心修复：绝对坐标 + 自身内部偏移）
    element_center_abs_x = element_abs_x + (element_width // 2)
    element_center_abs_y = element_abs_y + (element_height // 2)

    # 步骤3：计算需要滚动的偏移量（核心修复：抵消元素中心与窗口中心的位置差）
    # 滚动逻辑：滚动后，元素中心绝对坐标 - 窗口中心相对坐标 = 滚动后的视口偏移
    # 即：需要滚动的距离 = 元素中心绝对坐标 - 窗口中心相对坐标
    scroll_x = element_center_abs_x - viewport_center_x
    scroll_y = element_center_abs_y - viewport_center_y

    # 步骤4：修正滚动偏移量为整数，适配 scroll_from_origin 接口
    position: tuple[int, int] = (int(scroll_x), int(scroll_y))

    # 步骤5：执行滚动（确保 scroll_from_origin 是基于页面原点的滚动）
    # 若 scroll_from_origin 是基于视口滚动，可直接传入该 position；若有差异可微调
    options['value'] = position
    return self.scroll_from_origin(options)

  def scroll_from_origin(self,options:AbilityOpts)->bool:
    '''
    Scroll from an element by a given amount
    This scenario is effectively a combination of the above two methods.
    If the element is out of the viewport, it will be scrolled to the bottom of the screen, 
      then the page will be scrolled by the provided delta x and delta y values.
    Args:
      options (AbilityOpts): The scroll amount in the x and y directions.
    Returns:
      bool
    '''
    elem: WebElement | None = self._querier.query_element(options)
    if not elem:
      return False
    value:tuple[int,int] = options.get('value')
    scroll_origin = ScrollOrigin.from_element(elem)
    self._chains.scroll_from_origin(scroll_origin,*value).perform()
    return True
