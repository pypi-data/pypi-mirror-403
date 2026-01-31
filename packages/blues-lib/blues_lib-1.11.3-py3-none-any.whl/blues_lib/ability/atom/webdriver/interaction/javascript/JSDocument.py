from selenium.webdriver.remote.webdriver import WebDriver
from blues_lib.ability.atom.webdriver.interaction.javascript.JSBase import JSBase
from blues_lib.ability.atom.webdriver.interaction.javascript.JSCss import JSCss
from blues_lib.ability.atom.webdriver.interaction.javascript.JSScroll import JSScroll
from blues_lib.types.common import AbilityOpts

class JSDocument(JSBase):
  
  def __init__(self,driver:WebDriver):
    super().__init__(driver)
    self.js_css = JSCss(driver)
    self.js_scroll = JSScroll(driver)

  def set_inner_html(self,options:AbilityOpts)->bool: 
    '''
    Insert html to the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the html string
    Returns:
      bool : 
    '''
    html:str = options.get('value')
    script:str = '{return arguments[0].innerHTML=`%s`;}' % (html)
    options['value'] = script
    return self._set_document(options)
  
  def set_outer_html(self,options:AbilityOpts)->bool:
    '''
    Set the outer html of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the html string
    Returns:
      bool : 
    '''
    html:str = options.get('value')
    script:str = '{return arguments[0].outerHTML=`%s`;}' % (html)
    options['value'] = script
    return self._set_document(options)
  
  def set_inner_text(self,options:AbilityOpts)->bool:
    '''
    Get or set the text of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the text string
    Returns:
      str|None: the text of the element
    '''
    text:str = options.get('value')
    script:str = '{return arguments[0].innerText=`%s`;}' % (text)
    options['value'] = script
    return self._set_document(options)

  def append_inner_html(self,options:AbilityOpts)->bool:
    '''
    Append html to the inner html of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the html string
    Returns:
      bool : 
    '''
    html:str = options.get('value')
    script:str = '{const html = arguments[0].innerHTML; return arguments[0].innerHTML=html+`%s`;}' % (html)
    options['value'] = script
    return self._set_document(options)

  def append_inner_text(self,options:AbilityOpts)->bool:
    '''
    Append text to the inner text of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the text string
    Returns:
      bool : 
    '''
    text:str = options.get('value')
    script:str = '{const text = arguments[0].innerText; return arguments[0].innerText=text+`%s`;}' % (text)
    options['value'] = script
    return self._set_document(options)

  def remove_html(self,options:AbilityOpts)->bool:
    '''
    Remove the inner html of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (str): the html string
    Returns:
      bool : 
    '''
    script:str = 'return arguments[0].outerHTML=``;'
    options['value'] = script
    return self._set_document(options)

  def remove_text(self,options:AbilityOpts)->bool:
    '''
    Remove the inner text of the element
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      bool : 
    '''
    script:str = 'return arguments[0].innerText=``;'
    options['value'] = script
    return self._set_document(options)

  def set_value(self,options:AbilityOpts)->bool:
    options['value'] = {
      'value':options.get('value') or ''
    }
    return self.set_attribute(options)

  def set_attribute(self,options:AbilityOpts)->bool:
    '''
    Set the attribute of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (dict): the attribute dict
    Returns:
      bool :
    '''
    attr_set = []
    attrs:dict[str,str] = options.get('value')
    if not attrs:
      return False
    
    self.js_css.display(options)
    self.js_scroll.scroll_into_view(options)

    for attr_key, attr_value in attrs.items():
      attr_set.append(f"targetElem.setAttribute(`{attr_key}`, `{attr_value}`);")
    script:str = f"const targetElem = arguments[0]; {''.join(attr_set)}"

    opts:AbilityOpts = {**options,'value':script}
    return self._set_document(opts)
   
  def remove_attribute(self,options:AbilityOpts)->bool:
    '''
    Remove the attribute of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (list): the attribute list
    Returns:
      bool :
    '''
    attrs:list[str] = options.get('value')
    if not attrs:
      return False

    attr_set = []
    for attr_key in attrs:
      attr_set.append(f"targetElem.removeAttribute(`{attr_key}`);")
    script:str = f"const targetElem = arguments[0]; {''.join(attr_set)}"
    options['value'] = script
    return self._set_document(options)
