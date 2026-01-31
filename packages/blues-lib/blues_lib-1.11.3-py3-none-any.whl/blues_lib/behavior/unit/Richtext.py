from blues_lib.model.Model import Model
from blues_lib.behavior.Bean import Bean
from blues_lib.behavior.BhvExecutor import BhvExecutor

class Richtext(Bean):

  def _set(self)->any:
    # [{'type':'text','value':'xxx'},{'type':'image','value':'c:/xx.png'}]
    paras:list[dict] = self._config.get('value')
    if not paras or not isinstance(paras,list):
      return

    frame_loc_or_elem:str = self._config.get('frame_loc_or_elem')
    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'framein')
      
    self._setup()

    prev_para = {} 
    for para in paras:
      self._set_para(para,prev_para)
      prev_para = para

    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'frameout')
      
  def _setup(self):
    conf:dict = self._config.get('setup',{})
    bhv_chain:list[dict] = conf.get('bhv_chain')
    if not conf or not bhv_chain:
      return

    frame_loc_or_elem:str = conf.get('frame_loc_or_elem')
    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'framein')
      
    model = Model(bhv_chain)
    BhvExecutor(model,self._browser).execute()

    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'frameout')
      

  def _set_para(self,para:dict,prev_para:dict)->None:
    type = para.get('type')
    prev_type = prev_para.get('type')
    value = para.get('value')
    conf:dict = self._config.get(type,{})
    
    meta:dict = self._meta.get(type,{})
    bhv_chain:list[dict] = meta.get('bhv_chain')
    if not value or not bhv_chain:
      return
    
    frame_loc_or_elem:str = conf.get('frame_loc_or_elem')
    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'framein')
    
    # if the prev para is image, then add a empty line before the text
    if type=='text' and prev_type=='image':
      value = ['',value]

    bizdata = {
      **self._bizdata,
      "value":value
    }
    model = Model(bhv_chain, bizdata)
    BhvExecutor(model,self._browser).execute()

    if frame_loc_or_elem:
      self._switch(frame_loc_or_elem,'frameout')
  
  def _switch(self,frame_loc_or_elem:str,kind:str)->None:
    conf = {
      '_kind':kind,
      'loc_or_elem':frame_loc_or_elem
    }
    model = Model(conf)
    BhvExecutor(model,self._browser).execute()
