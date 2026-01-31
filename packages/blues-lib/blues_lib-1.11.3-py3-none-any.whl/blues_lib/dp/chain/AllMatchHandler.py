from blues_lib.dp.output.STDOut import STDOut
from blues_lib.dp.chain.Handler import Handler

class AllMatchHandler(Handler):

  def handle(self)->STDOut:

    stdout:STDOut = self.resolve()

    if self._next_handler:
      return self._next_handler.handle()
    else:
      return stdout

