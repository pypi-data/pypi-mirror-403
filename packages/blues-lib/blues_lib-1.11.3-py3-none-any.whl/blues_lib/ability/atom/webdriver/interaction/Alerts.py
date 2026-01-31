from selenium.webdriver.common.alert import Alert
from blues_lib.ability.atom.webdriver.wait.EC import EC
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.types.common import AbilityOpts

class Alerts(DriverAbility):

  def __init__(self,driver):
    super().__init__(driver)
    self._ec = EC(driver)

  def switch_to_alert(self,options:AbilityOpts|None=None)->Alert|None:
    '''
    Switch the driver's focus to the alert window
    Args:
      options (AbilityOpts): the options
    Returns:
      Alert|None : the alert element or None if not found
    '''
    stat:bool = self._ec.alert_is_present(options)
    if not stat:
      return None
    return self._driver.switch_to.alert

  def accept_alert(self,options:AbilityOpts|None=None)->str:
    return self._close_alert('accept',options)

  def dismiss_alert(self,options:AbilityOpts|None=None)->str:
    return self._close_alert('dismiss',options)

  def _close_alert(self,close_type:str='accept',options:AbilityOpts|None=None)->str:
    '''
    Accept the dialog
    The driver will back to main window automatically
    Returns:
      str : the alert's text
    '''
    alert:Alert|None = self.switch_to_alert(options)
    if not alert:
      return ''
    
    text:str = alert.text.strip()
    # not work on chrome
    value:str = options.get('value','') if options else ''
    if value:
      alert.send_keys(value)  

    if close_type == 'accept':
      alert.accept()
    else:
      alert.dismiss()
    return text