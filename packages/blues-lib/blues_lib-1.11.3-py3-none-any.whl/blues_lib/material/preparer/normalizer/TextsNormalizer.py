from blues_lib.util.Algorithm import Algorithm

class TextsNormalizer:
  
  @classmethod
  def handle(cls,paras:list[dict],config:dict)->list[dict]:
    return cls.get_length_valid_paras(paras,config)

  @classmethod
  def get_length_valid_paras(cls,paras:list[dict],config:dict)->list[dict]:
    max_length:int|None = config.get('max_length')
    if not paras or max_length is None:
      return paras
    
    new_paras:list[dict] = []
    cn_length:int = 0
    should_skip_text:bool = False
    for para in paras:
      type:str = para.get('type','')
      value:str = para.get('value','')
      if not value:
        continue

      if type != 'text':
        new_paras.append(para)
        continue

      if should_skip_text:
        continue

      text_length:int = Algorithm.get_cn_length(value)
      cn_length += text_length
      if cn_length <= max_length:
        new_paras.append(para)
      else:
        should_skip_text = True
    return new_paras