from blues_lib.material.preparer.MatPreparer import MatPreparer
from blues_lib.util.BluesURL import BluesURL
from blues_lib.util.Algorithm import Algorithm
from blues_lib.util.MatFiler import MatFiler
from blues_lib.util.BluesURL import BluesURL
from blues_lib.dp.output.STDOut import STDOut

class Localizer(MatPreparer):
  # 只处理数据，不区分trash

  def _handle_mat_thumb(self,entity:dict,config:dict)->tuple[bool,str]:
    is_success,message = self._download_image(entity,'mat_thumb',config)
    if not is_success:
      self._logger.info(f'{self.__class__.__name__} - {message}')
    return (True,'ok')

  def _handle_mat_paras(self,entity:dict,config:dict)->tuple[bool,str]:
    is_success,message = self._download_para_images(entity,'mat_paras',config)
    if not is_success:
      self._logger.info(f'{self.__class__.__name__} - {message}')
    return (True,'ok')

  def _handle_mat_images(self,entity:dict,config:dict)->tuple[bool,str]:
    is_success,message = self._download_para_images(entity,'mat_images',config)
    if not is_success:
      self._logger.info(f'{self.__class__.__name__} - {message}')
    return (True,'ok')

  def _download_para_images(self,entity:dict,field:str,config:dict)->tuple[bool,str]:
    paras: list[dict] = entity.get(field,[])
    image_max_length = config.get('image_max_length')
    if not paras:
      return (False,f'no {field}')

    image_count = 0
    new_paras = []
    messages: list[str] = []
    for para in paras:
      if para['type'] != 'image' and para['value']:
        new_paras.append(para)
        continue
      
      if not para['value']:
        continue
      
      if image_max_length is not None and image_count >= image_max_length:
        continue
      
      local_image,message = self._download(para['value'])

      if not local_image:
        messages.append(message)
        continue
        
      new_paras.append({**para,"value":local_image})
      image_count += 1

    entity[field] = new_paras
    return (True,'ok') if image_count>0 else (False,f'no valid new_paras - {messages}')

  def _download_image(self,entity:dict,field:str,config:dict)->tuple[bool,str]:
    image_url: str = entity.get(field,'')
    local_image,message = self._download(image_url)
    entity[field] = local_image
    return (True,'ok') if local_image else (False,message)

  def _download(self,image_url:str)->tuple[str,str]:
    if not BluesURL.is_http_url(image_url):
      return ('',f'not a http url - {image_url}')

    file_dir:str = BluesURL.get_main_domain(image_url)
    file_name:str = Algorithm.md5(image_url)

    stdout:STDOut = MatFiler.get_download_image(file_dir,file_name,image_url)
    if stdout.code!=200:
      return ('',stdout.message)
    return (stdout.data,'ok')
