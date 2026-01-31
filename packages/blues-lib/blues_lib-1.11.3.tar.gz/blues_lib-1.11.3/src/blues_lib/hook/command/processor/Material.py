from blues_lib.hook.command.CommandProc import CommandProc
from blues_lib.deco.CommandHookLog import CommandHookLog
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.material.chain.MatChain import MatChain

class Material(CommandProc):
  
  @CommandHookLog()
  def execute(self)->None:
    rule:dict = self._proc_conf.get('rule',{})
    entities:list[dict] = self._stdout.data or []

    request = {
      'rule':rule,
      'entities':entities, # must be a list
    }  
    handler = MatChain(request)
    stdout:STDOut = handler.handle()
    
    # remain the original code
    self._stdout.message = stdout.message
    self._stdout.data = stdout.data
    self._stdout.trash = stdout.trash