from blues_lib.namespace.CommandName import CommandName
from blues_lib.command.NodeCommand import NodeCommand
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.material.chain.MatChain import MatChain

class Engine(NodeCommand): 

  NAME = CommandName.Material.ENGINE

  def _invoke(self)->STDOut:
    rule:dict = self._summary.get('rule',{})
    entities:list[dict] = self._summary.get('entities',[])

    if not entities:
      raise ValueError(f'{self.NAME} : no input entities')

    if not rule:
      raise ValueError(f'{self.NAME} : no rule')

    request = {
      'rule':rule,
      'entities':entities, 
      'trash':[],
    } 
    handler = MatChain(request)
    return handler.handle()
 