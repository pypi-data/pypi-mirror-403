from blues_lib.dp.exception.matcher.MatcherException import MatcherException

class UnmatchedBreakException(MatcherException):
  # 自定义异常：matched 为 False，满足break条件, 停止执行之后的ability，但不向上抛出异常
  pass
