import random
from typing import Any

class CDPSetter:

  # 多UA随机选择（避免固定UA被识别）
  _USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  ]
  
  def __init__(self,driver,cdp_cmds:dict|None=None):
    self._driver = driver
    self._cdp_cmds = cdp_cmds or {}
    
  def set(self):
    default_cmds = self._get_default_cmds()
    cmds = {**default_cmds,**self._cdp_cmds}

    for k,v in cmds.items():
      if v is not None:
        self._driver.execute_cdp_cmd(k,v)

  def _get_default_cmds(self)->dict[str,Any]:
    # 随机选择一个UA
    user_agent = random.choice(self._USER_AGENTS)
    return {
      'Network.setUserAgentOverride':{
        # 设置用户代理
        'userAgent': user_agent
      },
      # 设置时区（模拟真实用户，避免UTC默认时区暴露）
      'Emulation.setTimezoneOverride': {
        'timezoneId': 'Asia/Shanghai'  # 中国时区，可根据需求调整
      },
      # 禁用性能检测（避免网站通过performance判断自动化）
      'Performance.disable': {},
      # 移除navigator上的webdriver标识
      'Page.addScriptToEvaluateOnNewDocument':{
        'source': """
          // 核心：移除webdriver标识
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined,
          configurable: false,  // 禁止网站重新定义
          writable: false
        });
          
        // 伪装语言/时区（模拟真实用户）
        Object.defineProperty(navigator, 'languages', {
          get: () => ['zh-CN', 'zh', 'en-US', 'en'],
          configurable: false
        });
        Object.defineProperty(navigator, 'language', {
          get: () => 'zh-CN',
          configurable: false
        });
          
        // 禁用自动化检测的API
        window.navigator.chrome = {
          runtime: {},
          loadTimes: () => ({})
        };
          
        // 伪装硬件并发数（避免暴露自动化环境）
        Object.defineProperty(navigator, 'hardwareConcurrency', {
          get: () => 8,  // 模拟8核CPU
          configurable: false
        });
          
        // 伪装设备内存（模拟真实电脑）
        Object.defineProperty(navigator, 'deviceMemory', {
          get: () => 16,  // 模拟16G内存
          configurable: false
        });
          
        // 禁用Canvas指纹（可选：随机化Canvas绘制结果）
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
          return originalToDataURL.call(this).replace(/[0-9a-f]{8}/, Math.random().toString(16).substring(2, 10));
        };
        
        // 禁用性能检测（避免 Remote 下性能特征暴露）
        delete window.performance.timing;
      """
    }
  }

