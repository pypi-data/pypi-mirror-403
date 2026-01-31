from blues_lib.util.ResourceReader import ResourceReader
from blues_lib.util.DotFileReader import DotFileReader
from blues_lib.types.common import LoginMode

class MetaTemplate:
  
  PACKAGE = 'blues_lib.metastore.template'

  @classmethod
  def read(cls, dot_path:str) -> dict:
    extension:str = 'conf'
    slash_path:str = DotFileReader.get_slash_path(dot_path,extension)
    return ResourceReader.read_hocon(cls.PACKAGE, slash_path)

  @classmethod
  def login(cls, login_mode:LoginMode) -> dict:
    dot_path:str = f'ability.login.{login_mode}.login'
    return cls.read(dot_path)

  @classmethod
  def login_ephemeral(cls, login_mode:LoginMode) -> dict:
    dot_path:str = f'ability.login.{login_mode}.perform'
    return cls.read(dot_path)