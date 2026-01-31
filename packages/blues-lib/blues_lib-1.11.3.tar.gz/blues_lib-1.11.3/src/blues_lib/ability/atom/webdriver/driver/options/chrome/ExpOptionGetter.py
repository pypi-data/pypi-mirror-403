from typing import Any
import os
from blues_lib.dp.file.File import File
class ExpOptionGetter:
  
  @classmethod
  def _get_download_prefs(cls)->dict[str,Any]:
    # 下载配置
    download_dir = os.path.normpath(File.get_dir_path('browser_download'))
    return {
      'download.default_directory':download_dir, # 下载目录, 默认 "C:\\Users\\Downloads"
      'download.prompt_for_download':False, # 是否提示下载路径, False（禁用提示，直接下载到默认目录）
      'download.directory_upgrade':True, # 自动升级下载目录权限
      'download.extensions_to_open':'', # 移除所有直接打开文件类型, such as: "pdf"（直接打开 PDF 文件，不下载）
      'safebrowsing.enabled':False, # 启用安全浏览（屏蔽危险文件）
      "safebrowsing.disable_download_protection": True,   # 允许下载"危险文件"（如 .exe）
    }

  @classmethod
  def get(cls)->dict[str,Any]:
    download_prefs = cls._get_download_prefs()
    prefs = {
      **download_prefs,
      # 禁用密码/表单自动填充（减少特征）
      'credentials_enable_service': False,
      'profile.password_manager_enabled': False,
      'autofill.enabled': False,

      # 禁用缓存/历史记录（避免多轮测试指纹一致）
      'browser.cache.disk.enable': False,
      'browser.history_expire_days': 1,
      'browser.sessionstore.enabled': False,

      # 禁用通知/弹窗（减少干扰）
      'profile.default_content_setting_values.notifications': 2,
      'profile.default_content_setting_values.geolocation': 2,
      'profile.default_content_setting_values.media_stream': 2,  # 禁用摄像头/麦克风
      'profile.default_content_setting_values.popups': 0, # 控制网页中通过 window.open() 或 <a target="_blank"> 触发的弹窗窗口  0 - Default, 1 - Allow, 2 - Block

      # 禁用翻译/自动更新（减少特征）
      'translate.enabled': False,
      'browser_update_notifications.enabled': False,
      
      # 界面设置
      'autofill.profile_enabled':False, # 启用自动填充表单, False（禁用）
      
      # 插件与扩展相关
      'plugins.plugins_disabled':[
        "Chrome PDF Viewer",       # 禁用内置 PDF 预览
        "Adobe Flash Player",      # 禁用 Flash
      ], # 禁用指定插件（需插件 ID）
      'plugins.always_open_pdf_externally':True, # PDF 直接下载（不预览）
      'profile.default_content_setting_values.plugins':1, # 插件全局权限,1（允许）或 2（阻止）
      
      # 资源加载: 0 - Default, 1 - Allow, 2 - Block
      'profile.default_content_setting_values.images':0, # 用户级别的图片加载控制,设置为 2 会阻止网页中的 <img> 图片加载, 不阻止 CSS 背景图（如 background-image）、Base64 内联图片、Canvas 绘制的图像。
      'profile.managed_default_content_settings.stylesheets': 0, # 阻止 CSS 加载
      'profile.managed_default_content_settings.javascript': 0, # 阻止 JavaScript 执行
    }
    return {
      # Setting the detach parameter to true will keep the browser open after the process has ended
      'detach':True,
      # 设置浏览器的首选项（Preferences）用于配置浏览器的默认行为，如禁用图片、设置下载目录等。
      'prefs':prefs, 
      # Chromedriver has several default arguments it uses to start the browser. If you do not want those arguments added, pass them into excludeSwitches.
      'excludeSwitches':[
        'enable-automation',  # 移除“Chrome正被自动化工具控制”提示
        'enable-logging'  # 禁用日志（避免敏感信息输出）
      ],
      # 禁用自动化扩展，避免被检测到自动化工具。在需要绕过反爬虫机制或自动化检测的场景中使用。
      'useAutomationExtension':False, 
    }