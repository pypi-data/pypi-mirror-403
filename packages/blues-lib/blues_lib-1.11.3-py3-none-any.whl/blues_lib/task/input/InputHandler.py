from typing import Any
from blues_lib.metastore.render.MetaRenderer import MetaRenderer
from blues_lib.task.input.XComMapper import XComMapper
from blues_lib.types.common import InputOpts,InputMapping,TaskDef

class InputHandler:
  
  @classmethod
  def handle(cls,definition:TaskDef,bizdata:dict,ti:Any)->tuple[TaskDef,dict]:
    definition:TaskDef = cls._render_input_def_without_bizdata(definition)
    bizdata:dict = cls._add_input_to_bizdata(definition,bizdata,ti)
    return definition,bizdata

  @classmethod
  def _render_input_def_without_bizdata(cls,definition:TaskDef)->dict:
    return MetaRenderer.render(definition)

  @classmethod
  def _add_input_to_bizdata(cls,definition:TaskDef,bizdata:dict,ti:Any)->dict:

    # Step1: render the input options
    input_opts = MetaRenderer.render_node('input',definition,bizdata)

    # Step: validate the input opts
    validate_tpl = 'except.input.task_input_opts'
    input_opts:InputOpts = MetaRenderer.render_and_validate_node(validate_tpl,'input',definition,bizdata)

    # Step2: map xcom data to the bizdata by input opts
    mappings:list[InputMapping]|None = input_opts.get('xcom')
    if mappings:
      XComMapper(mappings,bizdata,ti).handle()
    
    # Step3: replace the bizdata placeholder by itself
    return MetaRenderer.render_by_self(bizdata)
