from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.types.common import SeqHookOpts,SeqOpts,SeqHookOpts,AbilityOpts
from blues_lib.ability.atom.webdriver.interaction.Frame import Frame
from blues_lib.util.BluesDateTime import BluesDateTime

class SeqHook:
  def __init__(self,driver:WebDriver,options:SeqOpts,bizdata:dict[str,Any]|None=None):
    self._driver = driver
    validate_tpl = 'except.input.seq_hook_opts'
    self._before_opts:SeqHookOpts = MetaRenderer.render_and_validate_node(validate_tpl,'before',options,bizdata)
    self._after_opts:SeqHookOpts = MetaRenderer.render_and_validate_node(validate_tpl,'after',options,bizdata)
    self._frame:Frame = None
    
  def before(self)->None:
    hook_opts:SeqHookOpts = self._before_opts
    if hook_opts:
      self._sleep(hook_opts)
      self._switch(hook_opts)
  
  def after(self)->None:
    hook_opts:SeqHookOpts = self._after_opts
    if hook_opts:
      self._sleep(hook_opts)
    self._switch_back()

  def _switch(self,hook_opts:SeqHookOpts)->None:
    frame_opts:AbilityOpts = hook_opts.get('frame',{})
    if not frame_opts:
      return 

    self._frame = Frame(self._driver)
    stat:bool = self._frame.switch_to_frame(frame_opts)
    if not stat:
      self._frame = None
      raise Exception(f"Switch frame failed")
    
  def _switch_back(self)->None:
    if self._frame:
      self._frame.switch_to_default_content()
      self._frame = None

  def _sleep(self,hook_opts:SeqHookOpts)->None:
    sleep_duration:float = float(hook_opts.get('sleep',0))
    if sleep_duration > 0:
      BluesDateTime.count_down({
        'duration':sleep_duration,
        'title':f'Sleep {sleep_duration}s before seq cast',
      })