from typing import Any

class BizManager():

  @classmethod
  def add_index(cls,bizdata:dict[str,Any]|None,index:int)->dict[str,Any]:
    '''
    Add the index to the bizdata
    Args:
      bizdata: The bizdata to add the index to
      index: The index to add to the bizdata
    Returns:
      A shallow clone of the bizdata with the index added
    '''
    bizdata = bizdata or {}
    return {
      **bizdata,
      # add system variables
      '_index':index,
      '_no':index+1
    }

  @classmethod
  def add_item(cls,bizdata:dict[str,Any]|None,item:dict[str,Any]|None,index:int)->dict[str,Any]:
    '''
    Add the item and the index to the bizdata
    Args:
      bizdata: The bizdata to add the item to
      item: The item to add to the bizdata
      index: The index to add to the bizdata
    Returns:
      A shallow clone of the bizdata with the item added
    '''
    bizdata = bizdata or {}
    item = item or {}
    return {
      **bizdata,
      **item,
      # add system variables
      '_index':index,
      '_no':index+1
    }