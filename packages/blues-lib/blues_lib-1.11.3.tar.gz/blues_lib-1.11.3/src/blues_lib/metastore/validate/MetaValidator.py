from typing import Any
from blues_lib.metastore.validate.SchemaValidator import SchemaValidator

class MetaValidator:
  """
  Class for validating metadata against JSON Schema templates
  """

  @classmethod
  def validate_node(cls, key:str, instance:dict, schema:dict)->Any:
    node_meta:Any = instance.get(key)
    if not node_meta:
      raise ValueError(f"metadata must has a non-empty '{key}' field")
    cls.validate(node_meta, schema)
    return node_meta

  @classmethod
  def validate(cls, instance:Any, schema:dict)->Any:
    stat,message = SchemaValidator.validate(instance, schema)
    if not stat:
      raise ValueError(message)
    return instance

  @classmethod
  def validate_node_with_template(cls, key:str, instance:dict, tpl_path:str)->Any:
    node_meta:Any = instance.get(key)
    if not node_meta:
      raise ValueError(f"metadata must has a non-empty '{key}' field")
    cls.validate_with_template(node_meta, tpl_path)
    return node_meta

  @classmethod
  def validate_with_template(cls, instance:Any, tpl_path:str)->Any:
    stat,message = SchemaValidator.validate_with_template(instance, tpl_path)
    if not stat:
      raise ValueError(message)
    return instance

  @classmethod
  def validate_as_metadta(cls, instance:Any, schema:dict)->Any:
    stat,message = SchemaValidator.validate_as_metadta(instance, schema)
    if not stat:
      raise ValueError(message)
    return instance
