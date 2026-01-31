from mergedeep import merge
from blues_lib.dp.chain.LastMatchHandler import LastMatchHandler
from blues_lib.dp.output.STDOut import STDOut

class MatHandler(LastMatchHandler):
  
  _DEFAULT_RULE = {
    'filter':{
      'unique_field':'mat_url',
    },
    'persistor':{
      'method':'insert', # insert or update or delete
      'sources':['trash'], # entities or trash 
      'conditions':[], # for update and delete
      'extend':{},
      'inc_fields':[],
      'inc_pattern':'^mat_',
      'exc_fields':[],
      'exc_pattern':'',
    },
    'preparer':{
      "mat_thumb":{
        'image_location':'local', # local or online
        'image_min_width':500,
        'image_max_width':1000,
        'image_min_height':500,
        'image_max_height':1000,
      },
      'mat_title':{
        'min_length':10,
        'max_length':30,
      },
      'mat_paras':{
        'min_length':250,
        'max_length':1000,
        'image_location':'local', # local or online
        'image_min_length':1,
        'image_max_length':8,
        'image_min_width':500,
        'image_max_width':1000,
        'image_min_height':500,
        'image_max_height':1000,
      },
      'mat_texts':{
        'min_length':250,
        'max_length':1000,
      },
      'mat_images':{
        'image_location':'local', # local or online
        'image_min_length':1,
        'image_max_length':16,
        'image_min_width':500,
        'image_max_width':1000,
        'image_min_height':500,
        'image_max_height':1000,
      }
    },
  }
  
  def resolve(self)->STDOut:
    self._entities:list[dict] = self._request.get('entities') or []
    self._trash:list[dict] = self._request.get('trash') or []
    self._rule:dict = self._request.get('rule') or {}
    
    self._logger.info(f'{self.__class__.__name__} - input entities: {len(self._entities)} ; trash: {len(self._trash)}')
    
    if not self._entities and not self._trash:
      message:str = "no input entities and trash" 
      return self._get_output(500,message)
    
    if not self._RULE_NAME in self._rule:
      message:str = f'{self.__class__.__name__} no {self._RULE_NAME} config need to handle'
      return self._get_output(500,message)

    config:dict = self._get_merged_config()
    return self._calculate(config)
  
  def _get_merged_config(self)->dict:
    dft_config:dict = self._DEFAULT_RULE.get(self._RULE_NAME,{})
    orig_config:dict = self._rule.get(self._RULE_NAME,{})
    config:dict = merge({},dft_config,orig_config)
    return config
  
  def _set_entities(self,entities:list[dict])->STDOut:
    self._request['entities'] = entities
    
  def _set_trash(self,rows:list[dict])->STDOut:
    if not self._request.get('trash'):
      self._request['trash'] = []
    if rows:
      self._request['trash'].extend(rows)

  def _calculate(self,config:dict)->STDOut:

    valid_entities = []
    trash_entities = []

    for entity in self._entities:
      is_valid,message = self._handle_entity(entity,config)
      if is_valid:
        entity['mat_stat'] = 'available'
        valid_entities.append(entity)
      else:
        # just abandon the duplicate entity
        if message == 'duplicate':
          continue

        entity['mat_stat'] = 'invalid'
        entity['mat_remark'] = message
        trash_entities.append(entity)

    self._set_entities(valid_entities)
    self._set_trash(trash_entities)
    
    # output request's attr
    return self._get_output(200,message)
  
  def _get_output(self,code:int=200,message:str='')->STDOut:
    req_entities:list[dict] = self._request.get('entities',[])
    req_trash:list[dict] = self._request.get('trash',[])

    msg:str = f"{self._RULE_NAME} : valid {len(req_entities)} ; invalid {len(req_trash)}"
    msg = msg+'; '+message if message else msg
    return STDOut(code,msg,req_entities,req_trash)
  
  def _handle_entity(self,entity:dict,config:dict)->tuple[bool,str]:
    # optional template method
    pass
