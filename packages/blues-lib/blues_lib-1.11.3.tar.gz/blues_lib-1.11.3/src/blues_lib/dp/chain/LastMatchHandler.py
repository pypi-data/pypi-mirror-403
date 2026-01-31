from blues_lib.dp.output.STDOut import STDOut
from blues_lib.dp.chain.Handler import Handler

class LastMatchHandler(Handler):

  def handle(self)->STDOut:

    stdout:STDOut = self.resolve()
    # break the chain when meet the first error
    if stdout.code!=200:
      return stdout

    if self._next_handler:
      return self._next_handler.handle()
    else:
      return stdout
