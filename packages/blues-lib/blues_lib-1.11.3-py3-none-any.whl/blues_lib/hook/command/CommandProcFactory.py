from blues_lib.hook.ProcFactory import ProcFactory
from .processor.Dummy import Dummy
from .processor.Skipper import Skipper
from .processor.Blocker import Blocker
from .processor.Material import Material

class CommandProcFactory(ProcFactory):
  
  _PROC_CLASSES = {
    Dummy.__name__: Dummy,
      
    Skipper.__name__: Skipper,
    Blocker.__name__: Blocker,

    Material.__name__: Material,
  }