from abc import ABC
import random
from blues_lib.ability.sequence.BaseSeqAbility import BaseSeqAbility
from blues_lib.types.common import LoopOpts,IntervalValue
from blues_lib.util.BluesDateTime import BluesDateTime

class LoopAbility(BaseSeqAbility,ABC):

  def _log(self,which:str,attempts:int,results:int):
    self._logger.info(f'{self.__class__.__name__} loop {attempts} attempts by {which}, execute {results} times')
    
  def _sleep_by_interval(self,loop_opts:LoopOpts):
    interval:int|float = self._get_loop_interval(loop_opts)
    if interval>0:
      BluesDateTime.count_down({
        'duration':interval,
        'title':f'Wait {interval}s in seq loop '
      })

  def _get_loop_interval(self,loop_opts:LoopOpts)->int|float:
    interval:IntervalValue = loop_opts.get('interval')
    if not interval:
      return 0

    value:float = 0
    try: 
      if isinstance(interval,list):
        value= round(random.uniform(*interval), 1)
      else:
        value= float(interval)
    except ValueError:
      value= 0
    return value
