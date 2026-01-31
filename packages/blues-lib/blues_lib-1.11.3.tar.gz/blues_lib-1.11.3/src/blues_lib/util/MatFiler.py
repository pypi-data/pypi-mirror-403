import os,datetime
from blues_lib.dp.output.STDOut import STDOut
from blues_lib.dp.file.File import File
from blues_lib.util.BluesDateTime import BluesDateTime    
from blues_lib.util.FileDownloader import FileDownloader    

class MatFiler(File):
  
  # the material stack's root dir
  MATERIAL_DIR = 'material'
  MATERIAL_LOG_DIR = 'log'

  # the material statck's file
  STACK_FILE_NAME = 'stack.json'

  @classmethod
  def get_download_dir(cls,dirs=[]):
    today = BluesDateTime.get_today()
    subdirs = [cls.MATERIAL_DIR,today,*dirs]
    return cls.get_dir_path(subdirs)

  @classmethod
  def get_download_image(cls,file_dir,file_name,url)->STDOut:
    '''
    Download the image in the body
    Parameter:
      site {str} : the site's name
      file_name {str} : the material's file name
      url {str} : the image's online url
    '''
    if not file_dir or not file_name or not url:
      return STDOut(500,'Failed to download - The parameters file_dir,file_name,url are required',None)

    image_dir = cls.get_download_dir([file_dir])
    result = FileDownloader.download_one(url,image_dir,file_name)
    if result[0]==200:
      return STDOut(200,'Managed to download',result[1])
    else:
      return STDOut(500,f'Failed to download - {result[1]}',url)

  @classmethod
  def get_stack_file(cls):
    return cls.get_file_path(cls.MATERIAL_DIR,cls.STACK_FILE_NAME)
  
  @classmethod
  def get_stack_root(cls):
    return cls.get_dir_path(cls.MATERIAL_DIR)

  @classmethod
  def get_material_root(cls):
    return cls.get_dir_path(cls.MATERIAL_DIR)

  @classmethod
  def get_log_root(cls):
    return cls.get_dir_path(cls.MATERIAL_LOG_DIR)

  @classmethod
  def get_today_log_root(cls):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    root = cls.get_log_root()
    return os.path.join(root,today)
