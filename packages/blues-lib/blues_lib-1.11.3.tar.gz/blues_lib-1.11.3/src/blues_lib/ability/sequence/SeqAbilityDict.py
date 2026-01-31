from selenium.webdriver.remote.webdriver import WebDriver

# element 
from blues_lib.ability.sequence.StandardSeqAbility import StandardSeqAbility
from blues_lib.ability.sequence.loop.OrderAbility import OrderAbility
from blues_lib.ability.sequence.loop.PageAbility import PageAbility

from blues_lib.ability.sequence.loop.forby.ItemForAbility import ItemForAbility
from blues_lib.ability.sequence.loop.forby.CountForAbility import CountForAbility
from blues_lib.ability.sequence.loop.forby.ElementForAbility import ElementForAbility

class SeqAbilityDict():

  @classmethod
  def get(cls,driver:WebDriver)->dict:
    return {
      StandardSeqAbility.__name__:StandardSeqAbility(driver),
      OrderAbility.__name__:OrderAbility(driver),
      PageAbility.__name__:PageAbility(driver),

      ItemForAbility.__name__:ItemForAbility(driver),
      CountForAbility.__name__:CountForAbility(driver),
      ElementForAbility.__name__:ElementForAbility(driver),
    }