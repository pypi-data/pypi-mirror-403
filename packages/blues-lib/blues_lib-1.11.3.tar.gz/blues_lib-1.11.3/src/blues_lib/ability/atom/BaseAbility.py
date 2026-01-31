from abc import ABC
import logging

class BaseAbility(ABC):

  def __init__(self):
    self._logger = logging.getLogger('airflow.task')