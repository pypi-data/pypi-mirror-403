from blues_lib.dp.output.STDOut import STDOut
from blues_lib.dp.chain.Handler import Handler

class FirstMatchHandler(Handler):

  def handle(self)->STDOut:

    stdout:STDOut = self.resolve()
    
    # return the chain if meet the first success
    if stdout.code==200:
      return stdout

    if self._next_handler:
      return self._next_handler.handle()
    else:
      return stdout
