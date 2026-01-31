import re
from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.element.information.InfoBase import InfoBase
from blues_lib.types.common import AbilityOpts

class InfoAttr(InfoBase):

  def get_text(self,options:AbilityOpts)->str:
    '''
    Fetching element's text node value
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str         
    '''
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return ''

    text:str = elem.text.strip()
    MULTI_NEWLINE_PATTERN = re.compile(r'\n+')
    return MULTI_NEWLINE_PATTERN.sub('\n', text)

  def get_tag_name(self,options:AbilityOpts)->str:
    '''
    Fetching element's tag name
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str         
    '''
    elem:WebElement|None = self._querier.query_element(options)
    return elem.tag_name if elem else ''
  
  def get_property(self,options:AbilityOpts)->str|bool|None:
    '''
    Get element's property value
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str|bool|None
    '''
    key:str = options.get('value','')
    elem:WebElement|None = self._querier.query_element(options)
    return elem.get_property(key) if elem else None

  def get_attribute(self,options:AbilityOpts)->str:
    '''
    Fetching Attributes or Properties ： Get the value of the specified attribute or property of the element.
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str
    '''
    key:str = options.get('value','')
    elem:WebElement|None = self._querier.query_element(options)
    return elem.get_attribute(key) if elem else ''

  def value_of_css_property(self,options:AbilityOpts)->str:
    '''
    Fetching element's css attr's value
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str
    '''
    key:str = options.get('value','')
    elem:WebElement|None = self._querier.query_element(options)
    return elem.value_of_css_property(key) if elem else ''

  def get_value(self,options:AbilityOpts)->str:
    '''
    Fetching form element's value ： 
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str         
    '''
    options['value']='value'
    return self.get_attribute(options) or ''

  def get_inner_html(self,options:AbilityOpts)->str:
    '''
    Fetching element's text node value
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str         
    '''
    options['value']='innerHTML'
    html:str|None = self.get_attribute(options)
    return html.strip() if html else ''

  def get_outer_html(self,options:AbilityOpts)->str:
    '''
    Fetching element's outer html value
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      str          
    '''
    options['value']='outerHTML'
    html:str|None = self.get_attribute(options)
    return html.strip() if html else ''

  def get_images(self,options:AbilityOpts)->list[str]|None:
    '''
    Get all img urls from multiple elements
    Args:
      options (AbilityOpts) : the element query options
    Returns:
      list[str]|None : the url list
    '''
    elems:list[WebElement]|None = self._querier.query_elements(options)
    if not elems:
      return None

    urls = []
    for elem in elems:
      if url := elem.get_attribute('src'):
        urls.append(url)
    return urls if urls else None
