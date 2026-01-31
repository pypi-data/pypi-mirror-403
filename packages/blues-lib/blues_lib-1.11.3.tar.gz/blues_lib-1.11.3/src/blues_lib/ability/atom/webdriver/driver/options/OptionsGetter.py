from selenium import webdriver
from blues_lib.ability.atom.webdriver.driver.options.chrome.CapGetter import CapGetter
from blues_lib.ability.atom.webdriver.driver.options.chrome.ArgumentGetter import ArgumentGetter
from blues_lib.ability.atom.webdriver.driver.options.chrome.ExpOptionGetter import ExpOptionGetter
from blues_lib.ability.atom.webdriver.driver.options.chrome.ExtensionGetter import ExtensionGetter

class OptionsGetter():
  '''
  Class for create driver options
  Reference: https://www.selenium.dev/documentation/webdriver/drivers/options/
  '''

  def __init__(self,caps:dict|None=None,arguments:list[str]|None=None,exp_options:dict|None=None,extensions:list[str]|None=None):
    self._caps = caps or {}
    self._arguments = arguments or []
    self._exp_options = exp_options or {}
    self._extensions = extensions or []
  
  def udc(self)->webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    caps = {**CapGetter.get(),**self._caps}
    self._set_caps(options,caps)

    arguments = ArgumentGetter.get_for_udc() + self._arguments
    self._set_arguments(options,arguments)

    extensions = ExtensionGetter.get() + self._extensions
    self._set_extensions(options,extensions)

    # exp prefs download settings
    return options

  def chrome(self)->webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    caps = {**CapGetter.get(),**self._caps}
    self._set_caps(options,caps)
    
    arguments = ArgumentGetter.get() + self._arguments
    self._set_arguments(options,arguments)
    
    exp_options = {**ExpOptionGetter.get(),**self._exp_options}
    self._set_exp_options(options,exp_options)

    extensions = ExtensionGetter.get() + self._extensions
    self._set_extensions(options,extensions)

    return options

  def _set_caps(self,options,caps):
    if not caps:
      return
    for k,v in caps.items():
      if v is not None:
        setattr(options,k,v)

  def _set_arguments(self,options,arguments):
    if not arguments:
      return
    for v in arguments:
      if v is not None:
        options.add_argument(v)

  def _set_exp_options(self,options,exp_options):
    if not exp_options:
      return
    for k,v in exp_options.items():
      if v is not None:
        options.add_experimental_option(k,v)
        
  def _set_extensions(self,options,extensions):
    if not extensions:
      return
    for v in extensions:
      if v is not None:
        options.add_extension(v)
