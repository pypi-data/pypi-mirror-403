from selenium.webdriver.common.by import By

class LocatorCreator:
  """
  LocatorCreator class to create locator tuple from location string.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/locators/
  """

  _BY_STRATEGIES:dict = {
    'css_selector':By.CSS_SELECTOR,
    'xpath':By.XPATH,
    'id':By.ID,
    'name':By.NAME,
    'class_name':By.CLASS_NAME,
    'tag_name':By.TAG_NAME,
    'link_text':By.LINK_TEXT,
    'partial_link_text':By.PARTIAL_LINK_TEXT,
  }  

  @classmethod 
  def create(cls,location:str,by_name:str='')->tuple[str,str]|None:
    '''
    convert the location to the by and value tuple
    'css_selector:.name' -> (By.CSS_SELECTOR,'.name')
    '.name' -> (By.CSS_SELECTOR,'.name')
    'xpath://div' -> (By.XPATH,'//div')
    '//div' -> (By.XPATH,'//div')
    'div' -> (By.XPATH,'tag_name')
    
    @param {str} location - the element location with or without strategy prefix
    @param {str} by_name - specify a by strategy name
    '''
    if not location:
      raise ValueError(f'empty location')
    strategy:str = '' 
    selector:str = ''
    for key,value in cls._BY_STRATEGIES.items():
      if location.startswith(f'{key}:'):
        strategy = value
        selector = location[len(key)+1:]
        break
      
    if not strategy:
      strategy = cls._get_default_strategy(location,by_name)
      selector = location
      
    return (strategy,selector)
  
  @classmethod
  def _get_default_strategy(cls,location:str,by_name:str)->str:
    if by_name in cls._BY_STRATEGIES:
      return cls._BY_STRATEGIES[by_name]

    if location.startswith('//'):
      return By.XPATH
    return By.CSS_SELECTOR
