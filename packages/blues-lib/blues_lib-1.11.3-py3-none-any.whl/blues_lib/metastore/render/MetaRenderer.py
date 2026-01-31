from blues_lib.hocon.replacer.HoconReplacer import HoconReplacer 
from blues_lib.metastore.validate.SchemaValidator import SchemaValidator

class MetaRenderer():

  @classmethod
  def render(cls,definition:dict,bizdata:dict|None = None,config:dict|None = None)->dict:
    '''
    Base on a definition, render it with the bizdata
      - replace the environment variables ${var}
      - include the file  %{include a.b.c}
      - calcualte the function %{function fn_name}
      - replace the bizdata variables {{var}}
    Args:
      definition: The base data
      bizdata: The business data
      config: The replacer's config
    Returns:
      The deep cloned rendered definition
    '''
    if not definition:
      return {}
    return HoconReplacer(definition,bizdata,config).replace()

  @classmethod
  def render_and_validate(cls,validate_tpl:str,definition:dict,bizdata:dict|None = None,config:dict|None = None)->dict:
    meta:dict = cls.render(definition,bizdata,config)
    stat,message = SchemaValidator.validate_with_template(meta,validate_tpl)
    if not stat:
      raise ValueError(message)
    return meta

  @classmethod
  def render_by_self(cls,definition:dict)->dict:
    config:dict = {
      'keep_placeholder':True
    }
    return cls.render(definition,definition,config)

  @classmethod
  def render_node(cls,key:str,definition:dict,bizdata:dict|None = None,config:dict|None = None)->dict:
    '''
    render the definition node with the bizdata and config
    Args:
      key: The key of the definition node to render
      definition: the base data
      bizdata: The business data
      config: The replacer's config
    Returns:
      The deep cloned rendered definition node
    '''
    if not definition:
      return {}
    node_def:dict = definition.get(key,{})
    return MetaRenderer.render(node_def,bizdata,config) if node_def else {}

  @classmethod
  def render_and_validate_node(cls,validate_tpl:str,key:str,definition:dict,bizdata:dict|None = None,config:dict|None = None)->dict:
    '''
    render the definition node with the bizdata and config, and validate it with the schema
    Args:
      validate_tpl: The schema template path to validate the rendered node
      key: The key of the definition node to render
      definition: the base data
      bizdata: The business data
      config: The replacer's config
    Returns:
      The deep cloned rendered definition node
    '''
    node_meta:dict = cls.render_node(key,definition,bizdata,config)
    stat,message = SchemaValidator.validate_with_template(node_meta,validate_tpl)
    if not stat:
      raise ValueError(message)
    return node_meta