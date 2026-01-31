from selenium.webdriver.remote.webelement import WebElement
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.model.Model import Model
from blues_lib.namespace.CrawlerName import CrawlerName
from blues_lib.crawler.base.BaseCrawler import BaseCrawler
from blues_lib.hocon.replacer.HoconReplacer import HoconReplacer

class ForCrawler(BaseCrawler):

  NAME = CrawlerName.Engine.FOR

  def _get_entities(self)->list[dict]|None:
    '''
    Set the entities for for crawler
    @return {None}
    '''
    entities:list[dict] = self._summary_conf.get(CrawlerName.Field.ENTITIES.value) 
    if entities:
      return entities

    urls:list[dict] = self._summary_conf.get('urls') 
    if urls:
      return [{'url':url} for url in urls]

    for_element:str = self._summary_conf.get('for_element')
    if for_element:
      elements:list[WebElement] = self._browser.waiter.querier.query_all(for_element)
      if elements:
        return [{} for _ in elements]

    for_count:int = self._summary_conf.get(CrawlerName.Field.FOR_COUNT.value) or 1
    # pad a empty entity for each for count
    return [{} for _ in range(for_count)]
    
  def _crawl(self)->STDOut:
    '''
    override the crawl method
    execute the main crawler looply, by the entities or count
    @return {STDOut}
    '''
    self._entities:list[dict] = self._get_entities()

    repeat_count:int = int(self._summary_conf.get('repeat_count') or 1)
    results:list[any] = []
    for _ in range(repeat_count):
      output:STDOut = self._crawl_loop()
      if output.code != 200:
        return output
      
      results = results + output.data
    return STDOut(200,'ok',results)

  def _crawl_loop(self)->STDOut:
    '''
    override the crawl method
    execute the main crawler looply, by the entities or count
    @return {STDOut}
    '''
    if not self._crawler_meta:
      message = f'[{self.NAME}] Failed to crawl - Missing crawler config'
      return STDOut(500,message)

    if not self._entities:
      message = f'[{self.NAME}] Failed to crawl - Missing entities'
      return STDOut(500,message)
    
    try:
      results:list[any] = []
      index = 0
      for entity in self._entities:
        idx_entity = {}
        idx_entity['index'] = index
        index += 1
        idx_entity['no'] = index

        condition:list = self._summary_conf.get('for_skip')
        # must replace the loc's no placeholder
        condition = HoconReplacer(condition,idx_entity).format()
        skipable:bool = self._skip(condition)
        if skipable:
          self._logger.info(f'Skip the crawler: {condition}')
          continue

        # replace the entity's index placeholders
        entity = HoconReplacer(entity,idx_entity).format()
        # replace the bizdata's index placeholders
        biz = HoconReplacer(self._bizdata,idx_entity).format()
        
        # use the entity to cover the bizdata
        merged_entity = {**biz,**entity,**idx_entity}
        model = Model(self._crawler_meta,merged_entity)
        output:STDOut = self._invoke(model)
        # only save the data field
        if isinstance(output.data,list):
          results.extend(output.data)
        else:
          results.append(output.data)
        self._set_interval()
        
      return STDOut(200,'ok',results)
    except Exception as e:
      message = f'[{self.NAME}] Failed to crawl - {e}'
      return STDOut(500,message)
    