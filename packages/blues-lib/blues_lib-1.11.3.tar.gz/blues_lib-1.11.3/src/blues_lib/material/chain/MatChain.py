from blues_lib.dp.chain.AllMatchHandler import AllMatchHandler
from blues_lib.material.MatHandler import MatHandler
from blues_lib.dp.output.STDOut import STDOut

from blues_lib.material.filter.Deduplicator import Deduplicator

from blues_lib.material.preparer.Localizer import Localizer
from blues_lib.material.preparer.Normalizer import Normalizer
from blues_lib.material.preparer.Validator import Validator

from blues_lib.material.persistor.Mutator import Mutator

class MatChain(AllMatchHandler):

  _HANDLE_GROUP = {
    'filter':[Deduplicator],    
    'preparer':[Localizer,Normalizer,Validator], # ordered handlers
    'persistor':[Mutator],
  }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._chain_names:list[str] = []

  def resolve(self)->STDOut:
    handlers:list[MatHandler] = self._get_handlers()
    if not handlers:
      return STDOut(500,f'{self.__class__.__name__} failed to create a mateiral chain')
    
    chain:MatHandler = self._get_chain(handlers)
    self._logger.info(f'{self.__class__.__name__} create mat chan : {" -> ".join(self._chain_names)}')

    return chain.handle() 
  
  def _get_handlers(self)->list[MatHandler]:
    rule:dict = self._request.get('rule',{})
    if not rule:
      return []

    handlers:list[MatHandler] = []
    for key in rule.keys():
      group_handlers:list[MatHandler] = self._HANDLE_GROUP.get(key,[])
      for handler_class in group_handlers:
        handler:MatHandler = handler_class(self._request)
        handlers.append(handler)
        self._chain_names.append(handler_class.__name__)
    return handlers

  def _get_chain(self,handlers)->MatHandler:
    last_handler:MatHandler = handlers[0]
    for handler in handlers[1:]:
      last_handler.set_next(handler)
      last_handler = handler
    return handlers[0]
