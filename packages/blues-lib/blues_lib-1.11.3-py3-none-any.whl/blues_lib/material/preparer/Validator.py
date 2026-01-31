from blues_lib.material.preparer.MatPreparer import MatPreparer
from blues_lib.util.Algorithm import Algorithm
from blues_lib.util.BluesFiler import BluesFiler
from blues_lib.util.BluesURL import BluesURL

class Validator(MatPreparer):
  
  def _handle_mat_url(self,entity:dict,config:dict)->tuple[bool,str]:
    mat_url:str = entity.get('mat_url','')
    stat:bool = BluesURL.is_http_url(mat_url)
    return (stat,'ok') if stat else (stat,'mat_url is not http url')

  def _handle_mat_thumb(self,entity:dict,config:dict)->tuple[bool,str]:
    thumb:str = entity.get('mat_thumb','')
    return self._is_image_valid('mat_thumb',thumb,config)

  def _handle_mat_title(self,entity:dict,config:dict)->tuple[bool,str]:
    title:str = entity.get('mat_title','')
    return self._is_text_length_valid('mat_title',title,config)

  def _handle_mat_paras(self,entity:dict,config:dict)->tuple[bool,str]:
    paras:list[dict] = entity.get('mat_paras',[])
    valid,message = self._is_images_valid('mat_paras',paras,config)
    if not valid:
      return (valid,message)

    return self._is_paras_length_valid('mat_paras',paras,config)

  def _handle_mat_texts(self,entity:dict,config:dict)->tuple[bool,str]:
    paras:list[dict] = entity.get('mat_texts',[])
    return self._is_paras_length_valid('mat_texts',paras,config)

  def _handle_mat_images(self,entity:dict,config:dict)->tuple[bool,str]:
    paras:list[dict] = entity.get('mat_images',[])
    valid,message = self._is_images_valid('mat_images',paras,config)
    return (valid,message)
  
  def _is_text_length_valid(self,field:str,text:str,config:dict)->tuple[bool,str]:
    min_length = config.get('min_length')
    max_length = config.get('max_length')
    length:int = self._get_text_length(text)

    if min_length is not None and length<min_length:
      return (False,f"{field} too short : {length} < {min_length}")

    if max_length is not None and length>max_length:
      return (False,f"{field} too long : {length} > {max_length}")
    
    return (True,'ok')
    
  def _is_paras_length_valid(self,field:str,paras:list[dict],config:dict)->tuple[bool,str]:
    min_length = config.get('min_length')
    max_length = config.get('max_length')
    length:int = self._get_paras_length(paras)

    if min_length is not None and length<min_length:
      return (False,f"{field} too short : {length} < {min_length}")

    if max_length is not None and length>max_length:
      return (False,f"{field} too long : {length} > {max_length}")
    
    return (True,'ok')
  
  def _is_images_valid(self,field:str,paras:list[dict],config:dict)->tuple[bool,str]:
    min_length = config.get('image_min_length')
    max_length = config.get('image_max_length')
    length:int = 0
    for para in paras:
      p_type:str = para.get('type')
      p_value:str = para.get('value')  or '' # must be a str
      if p_type != 'image':
        continue
      stat,_ = self._is_image_valid(field,p_value,config)
      if not stat:
        continue
      length += 1

    if min_length is not None and length<min_length:
      return (False,f"{field} image too short : {length} < {min_length}")

    if max_length is not None and length>max_length:
      return (False,f"{field} image too long : {length} > {max_length}")
    
    return (True,'ok')
  
  def _is_image_valid(self,field:str,path:str,config:dict)->tuple[bool,str]:
    image_location:str = config.get('image_location')
    stat:bool = True
    message:str = 'ok'
    if image_location == 'local':
      stat = BluesFiler.exists(path)
      message = 'ok' if stat else f'no local {field} exists'
    elif image_location == 'online':
      stat = BluesURL.is_http_url(path)
      message = 'ok' if stat else f'no online {field} exists'
    else:
      stat = False
      message = f'{image_location} is not a supported image_location of {field}'
    return (stat,message)
  
  def _get_text_length(cls,text:str)->int:
    return Algorithm.get_cn_length(text)
    
  def _get_paras_length(cls,paras:list[dict])->int:
    size = 0
    for para in paras:
      p_type:str = para.get('type')
      p_value:str = para.get('value')  or '' # must be a str
      if p_type == 'text':
        size += Algorithm.get_cn_length(p_value)
    return size
    
    
    



     



     