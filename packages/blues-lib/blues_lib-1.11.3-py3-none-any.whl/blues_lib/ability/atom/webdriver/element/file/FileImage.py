from blues_lib.dp.file.File import File
from blues_lib.util.FileDownloader import FileDownloader    
from blues_lib.types.common import AbilityOpts
from blues_lib.ability.atom.webdriver.element.file.FileBase import FileBase

class FileImage(FileBase):

  def download_images(self,options:AbilityOpts)->list[str]|None:
    '''
    Download image from image element
    Args:
      options (AbilityOpts) : the element query options
        - value (list[str]) : the download dirs list
    Returns:
      str : the downloaded file path
    '''
    urls:list[str]|None = self._info.get_images(options)
    if not urls:
      return None

    default_dir = File.get_dir_path(['download','img']) 
    file_dir = options.get('value') or default_dir

    result:dict = FileDownloader.download(urls,file_dir)
    if result['code'] !=200:
      return None
    return result['files']
  