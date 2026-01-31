class ArgumentGetter:
  '''
  alternative arguments
  '--incognito', # [导致 new_window('tab') 打开新窗口而不是新标签页] 启用隐身模式（无痕模式），浏览器不会保存历史记录、缓存和 Cookie。 在需要隔离会话的测试场景中，如测试登录功能或避免缓存干扰。
  '--lang=zh-CN', # 系统语言 such as: zh-CN

  '--remote-debugging-port=9222' # 启用远程调试端口,Chrome 浏览器的启动参数，用于指定 Chrome 启动时监听的调试端口。 such as: 9222
  '--remote-debugging-address=127.0.0.1' # 指定 Chrome 监听调试连接的网络接口（IP 地址）。默认是本地 127.0.0.1 - 本地机器连接；0.0.0.0 允许任何设备通过 IP 地址和端口连接到 Chrome 的调试服务。

  '--user-data-dir=c:/blue_bib/user_data' # 用户信息目录，用于指定 Chrome 浏览器的用户数据目录。默认是 %USERPROFILE%/AppData/Local/Google/Chrome/User Data。

  '--enable-logging' # 启用浏览器日志输出。
  '--v=4' # 设置日志详细级别（1 为最低，9 为最高）such as: 1

  '--headless', # 启用无头模式，浏览器在后台运行，不显示可视化界面。适用于服务器环境或不需要可视化界面的自动化测试场景，如爬虫或持续集成（CI）环境。 
  '--blink-settings=imagesEnabled=false', # 禁用图片加载。在爬虫或测试中，禁用图片可以加快页面加载速度。完全禁用所有图片（包括 CSS 背景）
  '''

  @classmethod
  def get_for_udc(cls)->list[str]:
    return [
      '--disable-infobars'
    ]

  @classmethod
  def get(cls)->list[str]:
    return [
      # core settings
      '--start-maximized', # 启动浏览器时最大化窗口。can't use with --window-position

      # 禁用自动化特征
      '--disable-blink-features=AutomationControlled',  # 核心：禁用自动化检测
      '--disable-infobars',  # 隐藏“受自动化控制”提示
      '--no-sandbox',  # 禁用沙盒（兼容Linux/Docker，同时减少特征）
      '--disable-gpu',  # 禁用GPU加速（避免不同设备指纹差异）
      '--disable-dev-shm-usage',  # 禁用/dev/shm（兼容低内存环境）

      # 禁用扩展/插件（减少特征）
      '--disable-extensions',
      '--disable-extensions-api',
      '--disable-plugins',

      # 禁用敏感API（避免指纹检测）
      '--disable-webgl',  # 禁用WebGL（避免WebGL指纹）
      '--disable-webrtc',  # 禁用WebRTC（避免IP泄露/指纹）
      '--disable-battery-api',  # 禁用电池API（反爬常检测该API判断自动化）
      '--disable-hardware-media-key-handling',  # 禁用硬件媒体键（减少特征）

      # 禁用弹窗/干扰（避免操作中断）
      '--disable-notifications', # 禁用浏览器的通知功能。在测试或爬虫中，避免网站弹出通知干扰操作。
      '--disable-geolocation', # 禁用浏览器的定位功能。在测试或爬虫中，避免网站获取用户位置干扰操作。
      '--disable-translate', # 禁用浏览器的翻译功能。在测试或爬虫中，避免网站自动翻译干扰操作。
      '--disable-save-password-bubble', # 禁用浏览器的保存密码提示气泡。在测试或爬虫中，避免网站弹出保存密码提示干扰操作。
      '--no-default-browser-check', # 禁用默认浏览器检查。在测试或爬虫中，避免网站检查默认浏览器干扰操作。
      '--no-first-run', # 跳过 Chrome 的首次运行向导。在自动化测试中，避免首次运行向导干扰测试流程。
      '--disable-first-run-ui', # 禁用首次运行时的用户界面（如欢迎页面）。在自动化测试中，避免首次运行界面干扰测试流程。
      '--hide-crash-restore-bubble', # 隐藏浏览器崩溃后恢复页面的提示气泡。在自动化测试中，避免崩溃恢复提示干扰测试逻辑。
      '--disable-application-install-prompt', # 禁用应用安装提示。在测试中，避免网站提示安装应用干扰测试流程。
      '--disable-default-apps', # 禁用默认应用。

      # 安全/隐私（避免特征暴露）
      '--ignore-ssl-errors', # 忽略 SSL 证书错误。在测试或爬虫中，访问使用自签名证书的网站时使用。
      '--ignore-certificate-errors', # 忽略证书错误。在测试或爬虫中，访问使用无效证书的网站时使用。
      '--disable-features=VizDisplayCompositor,StrictTransportSecurity',  # 禁用合成器（减少指纹）,禁用严格的传输安全策略。在测试或爬虫中，访问使用 HTTP 协议的网站时使用。
      '--enable-features=NetworkServiceInProcess',  # 合并网络进程（模拟真实浏览器）
      '--disable-web-security', # 禁用同源策略（用于测试跨域请求）。
      '--allow-running-insecure-content', # 允许运行不安全的内容。
      '--disable-https-first-mode', # 禁用 HTTPS 优先模式。在测试或爬虫中，访问使用 HTTP 协议的网站时使用。
      
      # Remote 专属优化：禁用远端易出问题的特征
      '--disable-seccomp-sandbox',  # 禁用 seccomp 沙盒（Remote 容器环境兼容）
      '--disable-setuid-sandbox',  # 禁用 setuid 沙盒（避免远端权限问题）
      '--disable-popup-blocking',  # Remote 下拦截弹窗无法处理，直接禁用拦截（避免提示）: 拦截后会在地址栏弹出 “已阻止弹窗” 的提示条（Remote 下无法手动关闭，且提示条可能遮挡元素 / 触发反爬）
    ] 
    

