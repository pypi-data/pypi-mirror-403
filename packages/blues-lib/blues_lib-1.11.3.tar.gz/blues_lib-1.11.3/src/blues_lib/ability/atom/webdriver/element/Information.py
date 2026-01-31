from selenium.webdriver.remote.webelement import WebElement
from blues_lib.ability.atom.webdriver.element.information.InfoState import InfoState
from blues_lib.ability.atom.webdriver.element.information.InfoRect import InfoRect
from blues_lib.ability.atom.webdriver.element.information.InfoAttr import InfoAttr
from blues_lib.types.common import AbilityOpts

class Information(InfoState,InfoRect,InfoAttr):
  """
  Information class to get element information.
  Reference : https://www.selenium.dev/documentation/webdriver/elements/information/
  """
  def get_article(self,options:AbilityOpts)->dict[str,list[str]]:
    text:str = self.get_text(options)
    texts:list[str] = text.split('\n') if text else []

    image_options = {
      **options,
      'target':'img',
      'root':options['target'],
    }
    images:list[str] = self.get_images(image_options) or []
    return {
      'text':texts,
      'image':images,
    }

  def get_paras(self,options:AbilityOpts)->list[dict[str,str]]:
    article = self.get_article(options)
    paras:list[dict[str,str]] = []
    
    texts:list[str] = article['text']
    images:list[str] = article['image']
    
    if texts:
      for text in texts:
        paras.append({
          'type':'text',
          'value':text,
        })
    if images:
      for image in images:
        paras.append({
          'type':'image',
          'value':image,
        })
    return paras