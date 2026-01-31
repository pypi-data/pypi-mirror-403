import re
from blues_lib.material.MatHandler import MatHandler
from blues_lib.dao.material.MatMutator import MatMutator 
from blues_lib.dp.output.STDOut import STDOut

class Mutator(MatHandler):
  
  _RULE_NAME:str = 'persistor'
  _MUTATOR:MatMutator = MatMutator()
  
  def _calculate(self,config:dict)->STDOut:
    rows:list[dict] = self._get_rows(config)
    method:str = config.get('method')
    sources:list[str] = config.get('sources',[])
    conditions:list[dict] = config.get('conditions',[])

    if not rows:
      return self._get_output(200,f'no {sources} rows to {method}')

    if method == 'insert':
      stdout = self._insert(rows)
    elif method == 'update':
      stdout = self._update(rows,conditions)
    elif method == 'delete':
      stdout = self._delete(conditions)
    else:
      stdout = STDOut(500,f'no {method} method')
    return self._get_output(stdout.code,stdout.message)

  def _insert(self,rows:list[dict])->STDOut:
    return self._MUTATOR.insert(rows)

  def _update(self,rows:list[dict],conditions:list[dict])->STDOut:
    if not conditions:
      return self._get_output(500,'no conditions')

    # only update the first entity
    return self._MUTATOR.update(rows[0],conditions)

  def _delete(self,conditions:list[dict])->STDOut:
    if not conditions:
      return self._get_output(500,'no conditions')
    return self._MUTATOR.delete(conditions)

  def _get_typed_entities(self,sources:list[str])->list[dict]:
    total:list[dict] = []
    if 'entities' in sources:
      total.extend(self._entities or [])
    if 'trash' in sources:
      total.extend(self._trash or [])
    return total
    
  def _get_rows(self,config:dict)->list[dict]:
    sources:list[str] = config.get('sources',[])
    entities:list[dict] = self._get_typed_entities(sources)
    if not entities:
      return []
     
    extend_entity:dict = config.get('extend',{}) 
    inc_fields:list[str] = config.get('inc_fields',[])
    inc_pattern:str = config.get('inc_pattern','')
    exc_fields:list[str] = config.get('exc_fields',[])
    exc_pattern:str = config.get('exc_pattern','')

    new_entities:list[dict] = []
    for entity in entities:
      new_entity:dict = entity.copy()
      new_entity.update(extend_entity)
        
      # include and exclude the fields
      if inc_fields:
        new_entity = {k:v for k,v in new_entity.items() if k in inc_fields}

      if inc_pattern:
        new_entity = {k:v for k,v in new_entity.items() if re.match(inc_pattern,k)}

      if exc_fields:
        new_entity = {k:v for k,v in new_entity.items() if k not in exc_fields}

      if exc_pattern:
        new_entity = {k:v for k,v in new_entity.items() if not re.match(exc_pattern,k)}

      new_entities.append(new_entity)
    return new_entities
    

