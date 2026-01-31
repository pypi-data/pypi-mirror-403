from selenium.webdriver.remote.webelement import WebElement
from blues_lib.util.BluesFiler import BluesFiler
from blues_lib.util.BluesDateTime import BluesDateTime
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.element.file.FileBase import FileBase

class FileUpload(FileBase):

  def upload(self,options:AbilityOpts)->bool:
    '''
    Add one or multiple files to the file input element.
    Args:
      options (AbilityOpts): The element query options
        - value (str|list[str]): The file path or list of file paths to upload.
    Returns:
      bool
    '''
    value:str|list[str]|None = options.get('value')
    if not value:
      return False
    
    elem:WebElement|None = self._querier.query_element(options)
    if not elem:
      return False

    files:list[str] = value if type(value) == list else [value]

    exist_files:list[str]  = BluesFiler.filter_exists(files)
    if not exist_files:
      self._logger.info(f'{self.__class__.__name__} no exist files: {files}')
      return False

    self._logger.info(f'{self.__class__.__name__} upload files: {exist_files}')
    # make sure the file input element is visible
    self._javascript.display_and_scroll_into_view(options)

    interval:int|float = options.get('interval') or 2
    return self._upload(elem,exist_files,interval)

  def _upload(self,elem:WebElement,files:list[str],interval:int|float)->bool:
    is_multiple:bool = elem.get_property('multiple')
    if is_multiple:
      self._logger.info(f'{self.__class__.__name__} upload mode: multiple')
      self._upload_multiple(elem,files)
    else:
      self._logger.info(f'{self.__class__.__name__} upload mode: single')
      self._upload_one_by_one(elem,files)
    
    BluesDateTime.count_down({'duration':interval,'title':f'Uploading {len(files)} images'})
    return True

  def _upload_multiple(self,elem:WebElement,files:list[str])->None:
    # must join the file paths by \n
    file_lines = '\n'.join(files)
    elem.send_keys(file_lines)

  def _upload_one_by_one(self,elem:WebElement,files:list[str])->None:
    for file in files:
      elem.send_keys(file)
