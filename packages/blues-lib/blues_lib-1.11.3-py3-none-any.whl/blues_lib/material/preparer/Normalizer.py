from blues_lib.material.preparer.MatPreparer import MatPreparer
from blues_lib.material.preparer.normalizer.TextsNormalizer import TextsNormalizer
from blues_lib.material.preparer.normalizer.ImagesNormalizer import ImagesNormalizer
from blues_lib.material.preparer.normalizer.ImageNormalizer import ImageNormalizer
from blues_lib.material.preparer.normalizer.RequireddNormalizer import RequiredNormalizer

class Normalizer(MatPreparer):
  # 按要求对entity进行归一化处理，包括文本长度/图片数量/图片尺寸/补充必填项
  # 只处理数据，不区分trash

  def _handle_mat_chan(self,entity:dict,config:dict)->tuple[bool,str]:
    # 此处不截取超长标题，否则造成语义混乱，当作非法数据处理
    entity['mat_chan'] = config.get('value','')
    return (True,'ok')

  def _handle_mat_thumb(self,entity:dict,config:dict)->tuple[bool,str]:
    '''
    Normalize mat_thumb to a image url
    - if has no value, pick a image from the mat_paras
    '''
    RequiredNormalizer.set_thumb(entity)
    entity['mat_thumb'] = ImageNormalizer.handle(entity['mat_thumb'],config)

    return (True,'ok')

  def _handle_mat_url(self,entity:dict,config:dict)->tuple[bool,str]:
    mat_url:str = entity.get('mat_url','')
    if not mat_url:
      return (True,'no mat_url need to normalize')

    RequiredNormalizer.set_system_fields(entity)
    return (True,'ok')

  def _handle_mat_paras(self,entity:dict,config:dict)->tuple[bool,str]:
    '''
    Normalize mat_paras to a structured array
    - must be {'type':'text|image','value':str}
    - if has no images, use the mat_thumb as the first para image
    '''
    rows:list[dict] = entity.get('mat_paras',[])
    if not rows:
      return (True,'no mat_paras need to normalize')

    # 如果是llm获取的就是结构化数组无需转换
    paras:list[dict] = []
    if rows[0].get('type'):
      paras = rows
    else:
      for row in rows:
        image = row.get('image')
        text = row.get('text')
        if image:
          paras.append({'type':'image','value':image})
        else:
          paras.append({'type':'text','value':text})
    
    entity['mat_paras'] = paras
    RequiredNormalizer.set_paras(entity)

    entity['mat_paras'] = ImagesNormalizer.handle(entity['mat_paras'],config)
    entity['mat_paras'] = TextsNormalizer.handle(entity['mat_paras'],config)
    return (True,'ok')

  def _handle_mat_images(self,entity:dict,config:dict)->tuple[bool,str]:
    paras:list[dict] = entity.get('mat_images')
    if not paras:
      return (True,'no mat_images need to normalize')
   
    entity['mat_images'] = ImagesNormalizer.handle(paras,config)
    return (True,'ok')

  def _handle_mat_texts(self,entity:dict,config:dict)->tuple[bool,str]:
    paras:list[dict] = entity.get('mat_texts',[])
    if not paras:
      return (True,'no mat_texts need to normalize')

    entity['mat_texts'] = TextsNormalizer.handle(paras,config)
    return (True,'ok')
  
