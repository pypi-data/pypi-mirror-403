import time
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.interaction.javascript.JSBase import JSBase
from blues_lib.types.common import AbilityOpts

class JSScroll(JSBase):
  
  def scroll(self,options:AbilityOpts)->bool:
    '''
    Scroll the document to the specified position.
    Args:
      options (AbilityOpts): the javascript options
        - value (tuple[int,int]): the scroll position, (left,top)
    '''
    x,y = options.get('value')
    if x<0 and y<0:
      return False

    script = f"window.scrollTo({x},{y});"
    self.execute_script({'value':script})
    return True

  def scroll_to_bottom(self):
    '''
    Scroll the document to the bottom.
    '''
    size = self.get_document_size()
    self.scroll({'value':(0,size['height'])})
    return True

  def scroll_to_top(self):
    '''
    Scroll the document to the top.
    '''
    self.scroll({'value':(0,0)})
    return True
  
  def lazy_scroll_to_bottom(self,options:AbilityOpts)->bool:
    '''
    Scroll the document to the bottom, support the content was loaded lazy.
    Args:
      options (AbilityOpts): the javascript options
        - value.step (int): the scroll height one time
        - value.attempts (int): the max sroll times, -1 means scrolling to the bottom
        - interval (int): the interval time between each scroll, unit is second
    Returns:
      bool : 
    '''
    value:dict = options.get('value')
    step:int = value.get('step') # px
    attempts:int = value.get('attempts') # -1 is infinite
    interval:int = options.get('interval') # second
    step = int(step) if step else 500
    attempts = int(attempts) if attempts else -1
    interval = int(interval)*1000 if interval else 1000

    script='''
    // 最后一个参数是python程序自动传入的回调
    var callback = arguments[arguments.length-1];
    (function(){
      var scrollHeight = document.body.scrollTop; // 当前滚动条位置
      var step = %s;
      var interval = %s;
      var attempts = %s;
      var scrolledCount = 0;
      function scroll(){
        // 没有超过设置的最大次数，且与最新内容高度比较没有到底，继续执行
        var unreachedBottom = scrollHeight<document.body.scrollHeight-window.innerHeight;
        var shouldContinue = (attempts==-1 || scrolledCount<attempts);
        if(shouldContinue && unreachedBottom){
          scrolledCount++;
          scrollHeight += step;
          window.scroll(0,scrollHeight);
          document.title = scrollHeight;
          setTimeout(scroll,interval);
        }else{
          // 必须显式回调结束程序，否则程序会超时异常
          callback(scrollHeight);
        }
      }
      // 使用setTimeout程序是必须用异步函数，否则浏览器不会等待程序执行完毕就关闭
      setTimeout(scroll,interval);
    })();
    ''' % (step,interval,attempts)

    # 返回值是callback抛出值
    height:int = self.execute_async_script({'value':script})
    return True if height>0 else False

  def scroll_into_view(self,options:AbilityOpts)->bool:
    '''
    Scroll the element into the viewport.
    Args:
      options (AbilityOpts): the javascript options
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False

    # put the element in the center of the viewport
    script = """
    const callback = arguments[arguments.length - 1];
    const elem = arguments[0];

    // 1. 获取元素的边界信息（位置+尺寸）
    const rect = elem.getBoundingClientRect();
    // 计算元素中心坐标（相对于视口）
    const elemCenterX = rect.left + rect.width / 2;
    const elemCenterY = rect.top + rect.height / 2;

    // 2. 获取视口范围（窗口可视区域）
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    // 3. 判断元素中心是否在视口内（x: 0~viewportWidth，y: 0~viewportHeight）
    const isCenterInView = (
      elemCenterX >= 0 &&
      elemCenterX <= viewportWidth &&
      elemCenterY >= 0 &&
      elemCenterY <= viewportHeight
    );

    // 4. 仅当中心不在视口内时，才滚动到中心
    if (!isCenterInView) {
      elem.scrollIntoView({ block: `center`, inline: `center` });
    }

    // 执行异步回调
    callback();
    """

    js_options = {
      'value':script,
      'args':[elem]
    } 
    self.execute_async_script(js_options)
    time.sleep(0.2)
    return True
