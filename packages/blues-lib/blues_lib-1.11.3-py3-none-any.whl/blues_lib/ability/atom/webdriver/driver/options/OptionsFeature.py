import logging
class OptionsFeature():
  # update driver options by option features

  def __init__(self,options_kwargs:dict,cdp_cmds:dict):
    self._logger = logging.getLogger('airflow.task')
    self._options_kwargs = options_kwargs
    self._cdp_cmds = cdp_cmds
  
  def set(self,features:list[str]):
    # translate option features to driver options
    if not features:
      return
    
    self._logger.info(f"{self.__class__.__name__} wedriver features ⌜{','.join(features)}⌟")

    # page_load_strategy : normal eager none, by default it's eager
    if 'normal' in features:
      self._options_kwargs['caps'].update({'page_load_strategy': 'normal'})

    # don't load images
    if 'imageless' in features:
      self._options_kwargs['arguments'] += ['--blink-settings=imagesEnabled=false']

    # headless
    if 'headless' in features:
      self._options_kwargs['arguments'] += ['--headless']
      
    # mobile mode
    if 'mobile' in features:
      cmds = {
        'Emulation.setDeviceMetricsOverride': {
          "width": 430,
          "height": 932,
          "deviceScaleFactor": 3.0,  # iPhone 12 Pro 的缩放比例
          "mobile": True,
          "screenOrientation": {"angle": 0, "type": "portraitPrimary"}
        },
        'Emulation.setUserAgentOverride': {
          "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        },
      }
      self._cdp_cmds.update(cmds)
      