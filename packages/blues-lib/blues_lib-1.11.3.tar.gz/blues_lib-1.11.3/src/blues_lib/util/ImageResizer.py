import os
from PIL import Image

class ImageResizer():

  @classmethod
  def handle(cls, local_image: str, config: dict) -> tuple[bool,str]:
    is_ad,message = cls.is_ad_image(local_image,config)
    if is_ad:
      return (False,'')
    return cls.resize(local_image,config)

  @classmethod
  def is_ad_image(cls, local_image: str, config:dict ) -> tuple[bool,str]:
    """
    通过图片的长宽比判断是否为典型的广告图
    
    参数:
        local_image: 本地图片路径
        max_w_h_ratio: 最大宽高比阈值，默认3
        max_h_w_ratio: 最大高宽比阈值，默认3
        
    返回:
        bool: 如果长宽比超过阈值则返回True（认为是广告图），否则返回False
    """
    try:
      # 打开图片并获取尺寸
      max_w_h_ratio: int = config.get('max_w_h_ratio') or 4
      max_h_w_ratio: int = config.get('max_h_w_ratio') or 4

      with Image.open(local_image) as img:
        width, height = img.size
        
        # 避免除以零错误
        if width == 0 or height == 0:
          return False
        
        # 计算宽高比和高宽比
        width_height_ratio = width / height  # 宽/高
        height_width_ratio = height / width  # 高/宽
        
        # 判断是否超过阈值
        if width_height_ratio > max_w_h_ratio or height_width_ratio > max_h_w_ratio:
          return (True,f"图片 {local_image} 长宽比异常，宽高比: {width_height_ratio:.2f}, 高宽比: {height_width_ratio:.2f}")

        return (False,'ok')
        
    except FileNotFoundError:
      return (False,f"错误: 找不到图片文件 {local_image}")
    except Exception as e:
      return (False,f"分析图片时发生错误: {str(e)}")
    
  @classmethod
  def resize(cls, local_image: str, config: dict) -> tuple[bool,str]:
    """
    检查并按比例调整本地图片尺寸使其符合给定范围，统一保存为PNG格式
    参数:
        local_image: 本地图片路径
        rule: 包含尺寸范围配置的字典
    返回:
        str: 处理后的图片路径
    """
    if not local_image:
      return (False,'no local_image')

    # 从配置中获取尺寸范围，设置默认值
    image_max_width = config.get('image_max_width')
    image_min_width = config.get('image_min_width')
    image_max_height = config.get('image_max_height')
    image_min_height = config.get('image_min_height')

    if not image_max_width or not image_max_height or not image_min_width or not image_min_height:
      return (True,local_image)
    
    # 验证配置的有效性
    if image_min_width > image_max_width:
      image_min_width = image_max_width
    if image_min_height > image_max_height:
      image_min_height = image_max_height
    
    try:
      # 打开图片
      with Image.open(local_image) as img:
        # 获取当前图片尺寸
        current_width, current_height = img.size
        
        # 计算原始宽高比
        if current_height == 0:
          return local_image  # 避免除以零错误
        original_ratio = current_width / current_height
        
        new_width, new_height = current_width, current_height
        need_resize = False
        
        # 检查是否需要调整尺寸（按比例）
        # 情况1: 宽度超出最大值
        if current_width > image_max_width:
          new_width = image_max_width
          new_height = int(new_width / original_ratio)
          need_resize = True
        
        # 情况2: 高度超出最大值（在情况1调整后可能出现）
        if new_height > image_max_height:
          new_height = image_max_height
          new_width = int(new_height * original_ratio)
          need_resize = True
        
        # 情况3: 宽度小于最小值
        if current_width < image_min_width:
          new_width = image_min_width
          new_height = int(new_width / original_ratio)
          need_resize = True
        
        # 情况4: 高度小于最小值（在情况3调整后可能出现）
        if new_height < image_min_height:
          new_height = image_min_height
          new_width = int(new_height * original_ratio)
          need_resize = True
        
        # 处理特殊情况：如果一个边达到最小值后另一个边超过最大值，允许这种情况
        # 不需要额外处理，前面的逻辑已经允许这种情况发生
        
        # 无论是否需要调整尺寸，都处理格式
        original_format = img.format.upper() if img.format else ''
        is_png = original_format == 'PNG'
        
        # 处理图片尺寸（如果需要）
        if need_resize:
          processed_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
          processed_img = img.copy()

        # 处理图片格式（确保为PNG）
        if not is_png:
          # 构建新的文件名（替换原扩展名）
          base, _ = os.path.splitext(local_image)
          new_path = f"{base}.png"
          
          # 删除原文件，必须先删除再保存，有可能同名（扩展名为png，但是format是webp）
          os.remove(local_image)
          
          # 保存为PNG格式
          processed_img.save(new_path, format='PNG')
          
          # 更新路径为新路径
          local_image = new_path
        else:
          # 如果已是PNG且尺寸需要调整，直接覆盖
          if need_resize:
            processed_img.save(local_image, format='PNG')
        
        return (True,local_image)
        
    except FileNotFoundError:
      return (False,f"错误: 找不到图片文件 {local_image}")
    except Exception as e:
      return (False,f"处理图片时发生错误: {str(e)}")
