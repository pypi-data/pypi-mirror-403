from dataclasses import dataclass
from blues_lib.dp.output.STDOut import STDOut

@dataclass
class SQLSTDOut(STDOut):
  count: int = 0
  sql: str = ''
  lastid: any = None