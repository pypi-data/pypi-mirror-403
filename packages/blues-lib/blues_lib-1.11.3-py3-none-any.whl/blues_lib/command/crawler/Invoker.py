import logging
from blues_lib.sele.browser.chrome.ChromeFactory import ChromeFactory   
from blues_lib.crawler.CrawlerFactory import CrawlerFactory
from blues_lib.sele.browser.Browser import Browser
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.model.Model import Model

class Invoker():
  
  _logger = logging.getLogger('airflow.task')

  @classmethod
  def invoke(cls,model:Model,context:dict|None=None)->STDOut:
    browser = cls._get_browser(model,context)
    crawler = CrawlerFactory(model,browser).create()
    return crawler.execute()
  
  @classmethod
  def _get_browser(cls,model:Model,context:dict|None=None)->Browser:

    browser_conf:dict = model.config.get('browser') or {}
    if cls._should_use_context_browser(context,browser_conf):
      model.bizdata['quit'] = False # don't quit the browser in the context
      model.config['summary']['quit'] = False # don't quit the browser in the summary
      return context.get('browser')

    driver_config =  browser_conf.get('config') or {} # optional
    driver_options = browser_conf.get('options') or {} # optional
    browser = ChromeFactory(**driver_options).create(driver_config)
    if not browser:
      raise Exception(f'[{self.NAME}] fail to create the browser')
    return browser
  
  @classmethod
  def _should_use_context_browser(cls,context:dict|None=None,browser_conf:dict|None=None)->bool:
    if context and context.get('browser') and not browser_conf:
      cls._logger.info(f'[crawler {cls.__name__}] use the context browser')
      return True
    else: 
      cls._logger.info(f'[crawler {cls.__name__}] use the task browser')
      return False
