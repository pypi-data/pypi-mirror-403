from typing import Any
from abc import ABC
import logging
from blues_lib.ability.atom.webdriver.DriverAbilityFacade import DriverAbilityFacade
from blues_lib.dp.exception.matcher.MatchedBreakException import MatchedBreakException
from blues_lib.dp.exception.matcher.UnmatchedBreakException import UnmatchedBreakException
from blues_lib.dp.exception.matcher.MatchedThrowException import MatchedThrowException
from blues_lib.dp.exception.matcher.UnmatchedThrowException import UnmatchedThrowException
from blues_lib.types.common import AbilityOpts,AbilityCondition

class MatcherAbility(ABC):

  def __init__(self,driver):
    self._driver = driver
    self._facade = DriverAbilityFacade(driver)
    self._logger = logging.getLogger('airflow.task')

  def _raise_or_return(self,options:AbilityOpts,matched:bool,matcher:str,value:Any,expected:Any)->bool:
    condition:AbilityCondition = options.get('condition') or {}
    if 'break_if' in condition:
      if condition['break_if'] and matched:
        raise MatchedBreakException(matcher,matched,value,expected,condition)
      if not condition['break_if'] and not matched:
        raise UnmatchedBreakException(matcher,matched,value,expected,condition)

    if 'break_unless' in condition:
      if condition['break_unless'] and not matched:
        raise UnmatchedBreakException(matcher,matched,value,expected,condition)
      if not condition['break_unless'] and matched:
        raise MatchedBreakException(matcher,matched,value,expected,condition)

    if 'throw_if' in condition:
      if condition['throw_if'] and matched:
        raise MatchedThrowException(matcher,matched,value,expected,condition)
      if not condition['throw_if'] and not matched:
        raise UnmatchedThrowException(matcher,matched,value,expected,condition)

    if 'throw_unless' in condition:
      if condition['throw_unless'] and not matched:
        raise UnmatchedThrowException(matcher,matched,value,expected,condition)
      if not condition['throw_unless'] and matched:
        raise MatchedThrowException(matcher,matched,value,expected,condition)
    return matched