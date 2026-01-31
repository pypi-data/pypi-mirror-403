# 反爬虫配置
反爬虫配置的本质是消除自动化特征 + 模拟真实浏览器指纹 + 模仿人工行为，以下配置组合覆盖「Chrome 启动参数、DevTools (CDP) 指令、Selenium 高级配置、行为伪装」四大维度，适配 90% 以上的反爬场景。
- --disable-blink-features=AutomationControlled	禁用自动化控制标识	网站通过 window.navigator.webdriver 检测自动化
- CDP 注入移除webdriver	页面加载前覆盖标识	避免网站提前检测到 webdriver=true
- 随机 UA / 时区 / 语言	模拟真实用户环境	固定 UA / 时区是自动化的典型特征
- Canvas 指纹随机化	篡改 Canvas 绘制结果	网站通过 Canvas 生成唯一指纹识别爬虫
- 随机等待 / 滚动	模仿人工操作节奏	机械的快速点击 / 滚动是爬虫核心特征
- 禁用 WebGL/WebRTC	减少设备指纹维度	不同设备的 WebGL/WebRTC 指纹可唯一识别自动化
