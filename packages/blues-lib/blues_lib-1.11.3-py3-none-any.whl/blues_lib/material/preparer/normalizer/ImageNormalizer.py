import logging
from blues_lib.util.ImageResizer import ImageResizer

class ImageNormalizer:
  _logger = logging.getLogger('airflow.task')
   
  @classmethod
  def handle(cls,image:str,config:dict)->str:
    return cls.get_size_valid_image(image,config)

  @classmethod
  def get_size_valid_image(cls,image:str,config:dict)->str:
    if not image:
      return image
      
    is_valid,message_or_image = ImageResizer.handle(image,config)
    if not is_valid:
      cls._logger.info(f'image {image} resize failed, message: {message_or_image}')
      return ''
    return message_or_image
