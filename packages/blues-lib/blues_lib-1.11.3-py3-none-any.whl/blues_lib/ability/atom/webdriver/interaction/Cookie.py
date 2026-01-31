import time
from blues_lib.util.BluesURL import BluesURL  
from blues_lib.dp.file.File import File
from blues_lib.util.FileReader import FileReader
from blues_lib.util.FileWriter import FileWriter
from blues_lib.ability.atom.webdriver.DriverAbility import DriverAbility
from blues_lib.types.common import AbilityOpts

class Cookie(DriverAbility): 
  '''
  WebDriver API provides a way to interact with cookies
  Cookie doc: https://www.selenium.dev/documentation/webdriver/interactions/cookies/
  '''

  def read_cookies(self,options:AbilityOpts|None=None)->list[dict]|None:
    '''
    Read cookies from a local file
    Args:
      options (AbilityOpts) : the cookie query options
        - file (str) : the cookie file path
    Returns:
      list[dict] : the list of cookie entities
    '''
    options = options or {}
    filename:str  = options.get('value','')
    file_path = self._get_default_file(filename)
    cookies = FileReader.read_json(file_path)
    if cookies:
      self._logger.info(f'Managed to read cookies from {file_path}')
    else:
      self._logger.error(f'Failed to read cookies from {file_path}')
    return cookies

  def read_and_add_cookies(self,options:AbilityOpts|None=None)->bool:
    '''
    Read cookies from a local file and add to the current page
    Args:
      options (AbilityOpts) : the cookie query options
        - file (str) : the cookie file path
    Returns:
      bool : True if cookies are added successfully
    '''
    cookies = self.read_cookies(options)
    if cookies:
      self.replace_cookies({'value':cookies})
      return True
    else:
      return False

  def save_cookies(self,options:AbilityOpts)->str:
    '''
    Write cookies to a local file
    Args:
      options (AbilityOpts) : the cookie query options
        - value (list[dict]) : the list of cookie entities
        - file (str) : the cookie file path
    Returns:
      str : the cookie file path
    '''
    options = options or {}
    cookies = options.get('value',[])
    if not cookies:
      self._logger.error('Failed to save cookies, no cookies to save')
      return ''

    file_path = self._get_default_file()
    is_writed = FileWriter.write_json(file_path,cookies)

    if is_writed:
      self._logger.info(f'Managed to write cookies to {file_path}')
      return file_path
    else:
      self._logger.error(f'Failed to write cookies to {file_path}')
      return ''

  def get_and_save_cookies(self,options:AbilityOpts|None=None)->str:
    '''
    Save current page's cookies to a local file
    Args:
      options (AbilityOpts) : the cookie query options
        - file (str) : the cookie file path
    Returns:
      str : the cookie file path
    '''
    options = options or {}
    
    # wait for full cookies to be loaded
    timeout:int = options.get('timeout',1)
    time.sleep(timeout)

    cookies:list[dict] = self.get_cookies()
    if cookies:
      return self.save_cookies({**options,'value':cookies})
    else:
      self._logger.error('This site has no cookies')
      return ''

  def _get_default_file(self,filename:str='',extension='json'):
    current_url = self._driver.current_url
    domain = BluesURL.get_main_domain(current_url)
    filename = filename or domain
    default_file = File.get_file_path('cookie',filename,extension)
    return default_file 

  def get_cookie(self,options:AbilityOpts)->dict|None:
    '''
    Get a named cookie
    Args:
      options (AbilityOpts) : the cookie query options
        - value (str) : the cookie name
    Returns: 
      dict : {'domain': 'mp.163.com', 'httpOnly': True, 'name': 'NTESwebSI', 'path': '/', 'sameSite': 'Lax', 'secure': False, 'value': '2A7C7F8FCD65F7D74650E13D349C60CC'}
    '''
    key:str = options.get('value','')
    return self._driver.get_cookie(key) if key else None
      
  def get_cookies(self)->list[dict]|None:
    '''
    Get all cookies
    Returns: 
      list[dict] : [{'domain': 'mp.163.com', 'httpOnly': True, 'name': 'NTESwebSI', 'path': '/', 'sameSite': 'Lax', 'secure': False, 'value': '2A7C7F8FCD65F7D74650E13D349C60CC'}]
    '''
    return self._driver.get_cookies() or None

  def add_cookie(self,options:AbilityOpts)->bool:
    '''
      options (AbilityOpts) : the cookie add options
        - value (dict) : one cookie entity, it's a format cookie dict
    '''
    options['value'] = [options['value']]
    return self.add_cookies(options)

  def add_cookies(self,options:AbilityOpts)->bool:
    '''
    Add cookies to the current browsing context
    The list of accepted JSON key values : https://www.w3.org/TR/webdriver1/#cookies
    Args:
      options (AbilityOpts) : the cookie add options
        - value (list<dict> | dict) : one or multi cookie entities, it's a format cookie dict
        -[{'name':'sessionid', 'value':'1715957318'}]
    Returns:
      {bool} : True if the cookies are added, False otherwise
    '''
    count = 0
    entities = options.get('value',[])
    for entity in entities:
      if not entity.get('name'):
        continue
      if 'expiry' in entity:
        entity['expiry'] = int(entity['expiry'])
        del entity['expiry']
      count+=1
      #full_entity:dict = self._get_complete_entity(entity)
      self._driver.add_cookie(entity)
    return True if count > 0 else False

  def replace_cookies(self,options:AbilityOpts):
    '''
    Replace the current cookies with the new cookies
    Args:
      options (AbilityOpts) : the cookie replace options
        - value (list<dict>) : the new cookie entities - standard cookie dict feched by dirver.get_cookies()
    '''
    self._driver.delete_all_cookies()
    self.add_cookies(options)

  def set_cookies(self,options:AbilityOpts)->bool:
    '''
    Add cookies to the current browsing context
    Args:
      options (AbilityOpts) : the cookie set options
        - value (str|dict) : a string or dict cookies' key and value 
       - 'BIDUPSID=77884ECAEE62BDD2A4A723BEF544DCB2; PSTM=1715957318'
       - {'BIDUPSID':'77884ECAEE62BDD2A4A723BEF544DCB2', 'PSTM':'1715957318'}
    Returns:
      bool : True if the cookies are set, False otherwise
    '''
    cookies = options.get('value','')
    if not cookies:
      return False

    if type(cookies) == str:
      opts = self._get_entity_form_string(cookies)
      return self.add_cookies(opts)
    elif type(cookies) == dict:
      opts = self._get_entity_form_dict(cookies)
      return self.add_cookies(opts)
    else:
      return False

  def _get_complete_entity(self,entity:dict)->dict:
    '''
    Get the cookie complete parameter dict
    Parameter:
      entity (dict) : the cookie dict
    Returns:
      dict : the complete cookie entity
    '''
    default_entity:dict = self._get_default_entity()
    # copy the input dict
    input_entity = entity.copy()
    # make sure the value is str type
    input_entity['value'] = str(input_entity['value'])
    default_entity.update(input_entity)    
    return default_entity

  def _get_entity_form_dict(self,cookies:dict)->AbilityOpts:
    '''
    Convert the cookies string to the entity list
    Parameter:
      cookies_dict {dict} : A dict containing multiple cookie keys and values, such as:
        - {'BIDUPSID':'77884ECAEE62BDD2A4A723BEF544DCB2', 'PSTM':'1715957318'}
    Returns:
      AbilityOpts : the cookie entity list
    '''
    entities = []
    for name,value in cookies.items():
      entities.append({
        'name':name,
        'value':value,
      })
    return {
      'value':entities
    }

  def _get_entity_form_string(self,cookies:str)->AbilityOpts:
    '''
    Convert the cookies string to the entity list
    Parameter:
      cookies_string {str} : A string containing multiple cookie keys and values, such as:
        - 'BIDUPSID=77884ECAEE62BDD2A4A723BEF544DCB2; PSTM=1715957318'
    Returns:
      AbilityOpts : the cookie entity list
    '''
    entities = []
    kv_list = cookies.split(';')
    for k_v in kv_list:
      if not k_v:
        continue
      kv=k_v.split('=')
      # must be key=value string
      if len(kv)<2:
        continue
      name = kv[0].strip()
      value = kv[1].strip()
      entities.append({
        'name':name,
        'value':value,
      })
    return {
      'value':entities
    }
  
  def delete_cookie(self,options:AbilityOpts)->bool:
    '''
    Remove a cookie by name
    Args:
      options (AbilityOpts) : the cookie delete options
        - value (str) : cookie name
    Returns:
      bool : True if the cookie is removed, False otherwise
    '''
    key = options.get('value','')
    if key:
      self._driver.delete_cookie(key)
    return True
  
  def delete_all_cookies(self)->bool:
    '''
    Clear all cookies
    Returns:
      bool : True if all cookies are cleared, False otherwise
    '''
    self._driver.delete_all_cookies()
    return True

  def _get_default_entity(self)->dict:
    current_domain = BluesURL.get_main_domain(self._driver.current_url)
    return {
      'name':'',
      'value':'',
      'domain':'.%s' % current_domain, 
      'expires': '',
      'path': '/',
      'httpOnly': False,
      'hostOnly': False,
      'secure': False,
    }
