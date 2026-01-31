from blues_lib.ability.atom.webdriver.interaction.javascript.JSBase import JSBase
from blues_lib.types.common import AbilityOpts

class JSLoader(JSBase):

  def load_script(self,options:AbilityOpts)->bool:
    '''
    Load the js script asynchronously, and wait for the script to load completely.
    Args:
      url (str): the scirpt file's path
    '''
    url:str = options.get('value')
    var:str = options.get('var')
    if not url:
      return False

    if var and self.var_exists(options):
      return True

    # 在onload中执行callback，通知python js脚本已结束
    callback = "var callback = arguments[arguments.length-1];" 
    create_script:str = f"const sele_script=document.createElement('script');sele_script.src='{url}';"
    onload_script:str = f"sele_script.onload=function(){{callback();console.log('{url} loaded by the selenium!')}};"
    append_script:str = "const head=document.getElementsByTagName('head')[0];head.appendChild(sele_script);return true;"
    script:str = f"{callback} {create_script} {onload_script} {append_script}"
    # wait the script loaded, Determine whether it is complete according to the dynamic insertion mark 'selenium-dynamic-script'
    return self.execute_async_script({'value':script})

  def load_scripts(self,options:AbilityOpts)->bool:
    '''
    Load the js scripts asynchronously, and wait for the scripts to load completely.
    Args:
      scripts (list[str|dict[str,str]]): the js scripts list
        - dict[str,str] : the js script's path and the global var name
    '''
    scripts:list[str|dict[str,str]] = options.get('value')
    if not scripts:
      return False

    for script in scripts:
      if not script:
        continue

      if isinstance(script,str):
        self.load_script({'value':script})
        continue

      if isinstance(script,dict):
        self.load_script(script)

    return True

  def var_exists(self,options:AbilityOpts)->bool:
    '''
    Determines whether the variable is available.
    Args:
      options (AbilityOpts): the javascript options
        - var (str): variable name, Support attribute concatenation
       - 'navigator'
       - 'navigator.userAgent'
    Returns:
      bool: True if the variable is available, False otherwise.
    '''
    var:str = options.get('var')
    if not var:
      return False

    script:str = f"return !!window.{var};"
    return self.execute_script({'value':script})

  def load_jquery(self):
    url:str = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js'
    var:str = 'jQuery'
    self.load_script({'value':url,'var':var})
