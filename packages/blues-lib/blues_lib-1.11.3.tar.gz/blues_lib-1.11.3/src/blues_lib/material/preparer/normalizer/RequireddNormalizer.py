import logging
from blues_lib.util.BluesURL import BluesURL
from blues_lib.util.Algorithm import Algorithm

class RequiredNormalizer:
  _logger = logging.getLogger('airflow.task')

  @classmethod
  def set_system_fields(cls,entity:dict):
    mat_url:str = entity.get('mat_url')
    entity['mat_site'] = BluesURL.get_main_domain(mat_url)
    entity['mat_id'] = Algorithm.md5(mat_url)

  @classmethod
  def set_paras(cls,entity:dict):
    paras:list[dict] = entity.get('mat_paras',[])
    thumb:str = entity.get('mat_thumb','')
    image_count:int = 0
    for para in paras:
      if para['type'] == 'image' and para['value']:
        image_count += 1
        break

    if image_count == 0 and thumb:
      paras.insert(0,{'type':'image','value':thumb})
  
  @classmethod
  def set_thumb(cls,entity:dict)->None:
    paras:list[dict] = entity.get('mat_paras',[]) or entity.get('mat_images',[])
    thumb:str = entity.get('mat_thumb','')
    if thumb or not paras:
      return None

    for para in paras:
      if para['type'] == 'image' and para['value']:
        entity['mat_thumb'] = para['value']
        break
