from typing import Any

class CapGetter:

  @classmethod
  def get(cls)->dict[str,Any]:
     # These capabilities are shared by all browsers.
    common_caps = {
      # DOM access is ready, but other resources like images may still be loading
      'page_load_strategy': 'eager',
      # This capability checks whether an expired (or) invalid TLS Certificate is used while navigating during a session.
      'accept_insecure_certs': True,
      # This capability sets the amount of time the driver should wait when trying to find an element if it is not immediately present.
      'timeouts': {
        'implicit': 0, # This specifies the time to wait for the implicit element location strategy when locating elements. The default timeout is 0ms 
        'pageLoad': 60000, # Specifies the time interval in which web page needs to be loaded in a current browsing context. The default timeout is 300,000ms
        'script': 30000, # Specifies when to interrupt an executing script in a current browsing context. The default timeout is 30,000ms
      },
      # Specifies the state of current session’s user prompt handler. Defaults to dismiss and notify state
      # 它不会主动去检测和关闭弹框，只有当你执行下一个 WebDriver 操作（比如点击、输入、跳转）时，Selenium 发现有未处理的弹框，才会触发这个兜底策略。
      'unhandled_prompt_behavior':'accept',
      # This new capability indicates if strict interactability checks should be applied to input type=file elements. As strict interactability checks are off by default, there is a change in behaviour when using Element Send Keys with hidden file upload controls.
      'strict_file_interactability':False,
      # This capability specifies the proxy configuration to be used for the session. If not specified, the driver will not use any proxy.
      'proxy':None,
    }
    caps = {
      # The binary parameter takes the path of an alternate location of browser to use.
      'binary_location':None,
      # debugger_address（ChromeOptions 专属属性）
      # 核心作用：让 Selenium 跳过启动新 Chrome 实例的流程，直接连接到已启动且开启远程调试的 Chrome 浏览器实例
      # 使用前提：
      # 1. 目标 Chrome 实例必须通过「远程调试端口」启动（如：chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile）；
      # 2. 需保证该 Chrome 实例未被其他 Selenium 会话占用，且端口可访问（本地常用 127.0.0.1:9222，远程需开放对应端口）；
      # 关键特性：
      # 1. 非启动属性：仅用于连接已有实例，不会触发 Chrome 启动，无实例时会抛出连接失败异常；
      # 2. Selenium 封装属性：不属于 Chrome 原生启动参数，是 Selenium 为简化远程调试连接设计的专属属性，需通过 options.debugger_address = "IP:端口" 配置；
      # 3. 会话复用：连接后可复用已有浏览器的 Cookie、登录状态、标签页等，适合调试/免重复登录场景；
      # 使用限制：
      # - 仅支持 Chrome 浏览器（Firefox/Edge 有各自的远程调试配置方式）；
      # - 连接后 Selenium 对浏览器的控制权有限（如无法修改部分启动参数）；
      # - Remote 场景下需保证调试端口可跨网络访问，且目标 Chrome 实例允许远程连接。
      'debugger_address': None,  # 示例值："127.0.0.1:9222"
    }
    return {**common_caps,**caps}