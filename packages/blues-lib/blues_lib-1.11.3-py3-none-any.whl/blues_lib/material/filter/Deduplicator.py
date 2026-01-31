from blues_lib.material.MatHandler import MatHandler
from blues_lib.dao.material.MatQuerier import MatQuerier

class Deduplicator(MatHandler):

  # remove the duplicate entities don't append into the trash
  _RULE_NAME = 'filter'
  _ERROR = 'duplicate'
  
  def _handle_entity(self,entity:dict,config:dict)->tuple[bool,str]:
    querier = MatQuerier()
    field:str = config.get('unique_field')
    value = entity.get(field)

    if not value or querier.exist(value,field):
      self._log_error(field,value)
      return (False,self._ERROR)

    return (True,'ok')
  
  def _log_error(self,field:str,value:any):
    self._logger.info(f"{self.__class__.__name__} abandon a duplicate entity, field: {field}, value: {value}")