import time,datetime,random
from blues_lib.util.BluesConsole import BluesConsole
import random
import time
import datetime

class BluesDateTime():

  spend = 0

  @classmethod
  def get_random_seconds(cls,min_seconds: float, max_seconds: float) -> float:
    """
    生成指定范围内的随机等待时间（秒）
    
    参数:
      min_seconds (float): 最小等待时间（秒）
      max_seconds (float): 最大等待时间（秒）
      
    返回:
      float: 随机等待时间，单位为秒，介于min_seconds和max_seconds之间
    """
    # 确保最小值小于等于最大值
    if min_seconds > max_seconds:
      min_seconds, max_seconds = max_seconds, min_seconds
    
    # 生成指定范围内的随机浮点数
    return random.uniform(min_seconds, max_seconds)

  @classmethod
  def get_today(cls):
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')

  @classmethod
  def get_time(cls):
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S')

  @classmethod
  def get_now(cls):
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')

  @classmethod
  def get_timestamp(cls):
    now = datetime.datetime.now()
    return int(now.timestamp() * 1000)

  @classmethod
  def count_down(cls,payload={}):
    '''
    @description : count down
    @param {int} payload.duration  : duration seconds
    @param {int} payload.interval  : interval seconds
    @param {str} payload.title  : title
    @param {bool} payload.printable  : print in the console
    '''

    duration = int(payload.get('duration',10))
    interval = int(payload.get('interval',1))
    title = payload.get('title','coutdown')

    if not duration:
      return

    if interval <=0:
      interval =1

    spend = 0
    time.sleep(interval)
    while spend < duration:
      spend += interval
      progress = (spend / duration) * 100
      remaining = duration - spend
      # 核心：构造统一长度的打印内容，用空格填充至固定长度（关键行）
      print_content = f"{title}: progress {progress:.0f}% | remain {remaining:.0f}s"
      # 计算最长内容的长度（100%时的长度，可手动指定或动态计算）
      max_length = len(f"{title}: progress 100% | remain 0s")
      # 左对齐+空格填充，确保所有内容长度=max_length
      print_content_padded = print_content.ljust(max_length)
      # 原有打印逻辑不变
      print(print_content_padded, end='\r', flush=True)
      if spend < duration:
        time.sleep(interval)
    # 循环结束换行
    print()