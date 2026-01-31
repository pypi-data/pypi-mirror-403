import logging
from blues_lib.util.ImageResizer import ImageResizer

class ImagesNormalizer:
  _logger = logging.getLogger('airflow.task')
   
  @classmethod
  def handle(cls,paras:list[dict],config:dict)->list[dict]:
    temp_paras = cls.get_length_valid_paras(paras,config)
    return cls.get_size_valid_paras(temp_paras,config)

  @classmethod
  def get_size_valid_paras(cls,paras:list[dict],config:dict)->tuple[bool,str]:
    if not paras:
      return paras

    new_paras = []
    for para in paras:
      if para['type'] != 'image':
        new_paras.append(para)
        continue
      
      is_valid,message_or_image = ImageResizer.handle(para['value'],config)
      if not is_valid:
        cls._logger.info(f'image {para["value"]} resize failed, message: {message_or_image}')
        continue

      new_paras.append({**para,'value':message_or_image})
    return new_paras

  @classmethod
  def get_length_valid_paras(cls,paras:list[dict],config:dict)->list[dict]:
    max_length:int|None = config.get('image_max_length')
    if not paras or max_length is None:
      return paras
    
    new_paras:list[dict] = []
    image_length:int = 0
    should_skip_image:bool = False
    for para in paras:
      type:str = para.get('type','')
      value:str = para.get('value','')
      if not value:
        continue

      if type != 'image':
        new_paras.append(para)
        continue

      if should_skip_image:
        continue

      image_length += 1
      if image_length <= max_length:
        new_paras.append(para)
      else:
        should_skip_image = True
    return new_paras