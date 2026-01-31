from blues_lib.dp.exception.matcher.MatcherException import MatcherException

class UnmatchedThrowException(MatcherException):
  # 自定义异常：matched 为 False，满足throw条件, 抛出异常
  pass
