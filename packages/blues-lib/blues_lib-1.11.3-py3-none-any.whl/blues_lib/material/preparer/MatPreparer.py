from blues_lib.material.MatHandler import MatHandler

class MatPreparer(MatHandler):
  
  _RULE_NAME = 'preparer'

  def _handle_entity(self,entity:dict,config:dict)->tuple[bool,str]:
    for field,field_config in config.items():
      method = getattr(self,f'_handle_{field}',None)
      if not method:
        continue
      is_valid,message = method(entity,field_config)
      if not is_valid:
        return (is_valid,message)
    return (True,'ok')

  def _get_merged_config(self)->dict:
    merged_config:dict = super()._get_merged_config()
    orig_config:dict = self._rule.get(self._RULE_NAME,{})
    # preparer通过属性名控制检查项，只保留orig_config中有的项
    new_config:dict = {}
    for field in merged_config.keys():
      if field in orig_config:
        new_config[field] = merged_config[field]
    return new_config
    

