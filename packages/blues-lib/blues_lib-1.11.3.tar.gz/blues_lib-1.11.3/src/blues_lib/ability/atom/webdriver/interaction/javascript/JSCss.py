from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.interaction.javascript.JSBase import JSBase
from blues_lib.types.common import AbilityOpts

class JSCss(JSBase):

  def set_inline_style(self,options:AbilityOpts)->bool:
    '''
    Set the style of the element
    Args:
      options (AbilityOpts): the javascript options
        - value (dict): the style dict
    Returns:
      bool :
    '''
    attr_set = []
    styles:dict[str,str] = options.get('value')
    if not styles:
      return False

    for attr_key, attr_value in styles.items():
      attr_set.append(f"{attr_key}:{attr_value};")
    script = f"const targetElem = arguments[0]; targetElem.style.cssText+=`{''.join(attr_set)}`;"

    options['value'] = script
    return self._set_document(options)

  def set_head_style(self,options:AbilityOpts)->bool:
    """
    将样式字典转换为动态插入<head>的JS脚本字符串（模板字符串简化引号）
    Args:
      options (AbilityOpts): the javascript options
        - value (dict): the style dict
    Returns:
      bool :
    """
    elem_styles:dict|str = options.get('value')
    if not elem_styles:
      return False

    if isinstance(elem_styles,str):
      css_text = elem_styles
    else:
      css_rules = []
      for selector, styles in elem_styles.items():
        if isinstance(styles,str):
          style_value = styles
        else:
          style_items = [f"{k}: {v};" for k, v in styles.items()]
          style_value = ''.join(style_items)
        css_rule = f"{selector} {{ {style_value} }}"
        css_rules.append(css_rule)
      css_text = ''.join(css_rules)
    
    script = f"""
    let styleTag = document.querySelector('style[data-custom-style="true"]');
    if (!styleTag) {{
      styleTag = document.createElement('style');
      styleTag.type = 'text/css';
      styleTag.setAttribute('data-custom-style', 'true');
      document.head.appendChild(styleTag);
    }}
    styleTag.textContent = `${{styleTag.textContent.trim()}} {css_text}`;
    return true;
    """
    options['value'] = script
    return self.execute_script(options)
  
  def mark(self,options:AbilityOpts)->bool:
    '''
    Highlight the element
    Args:
      options (AbilityOpts): the javascript options
    Returns:
      bool :
    '''
    script = '{return arguments[0].style[`background-color`]=`#FFFF00`;}'
    options['value'] = script
    return self._set_document(options)
  
  def hide(self, options:AbilityOpts) -> bool:
    target:str = options.get('target') or ''
    if not target:
      return False

    elem_styles:dict = {
      target:{
        'display': 'none!important',
      }
    }
    self.set_head_style({'value':elem_styles})
    return True

  def display(self, options:AbilityOpts) -> bool:
    """
    Show the element
    Args:
      options (AbilityOpts): the javascript options
        - value (dict|None): the style dict
    Returns:
      bool: True - 元素处理并设置可见成功；False - 元素未找到/无效或设置失败
    """
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False

    highlight_styles:dict = {
      'outline': '3px double #FFC107',
    }
    remove_outline_script = 'setTimeout(function() {targetElem.style.outline = ``;},1000)'
    if elem.is_displayed():

      outline:str = highlight_styles['outline']
      script = f"const targetElem = arguments[0]; targetElem.style.outline=`{outline}`; {remove_outline_script}; return true;"
    else:
      styles = {
        **highlight_styles,
        'display': 'inline-block',
        'visibility': 'visible',
        'opacity': '1',
        'z-index': '9999',
        'min-height': '16px',
        'min-width': '16px',
      }
      script = f"const targetElem = arguments[0]; targetElem.style.cssText+=`{''.join([f'{k}:{v};' for k,v in styles.items()])}`; {remove_outline_script}; return true;"

    opts:AbilityOpts = {
      'value':script,
      'args':[elem],
    }
    return self.execute_script(opts)
