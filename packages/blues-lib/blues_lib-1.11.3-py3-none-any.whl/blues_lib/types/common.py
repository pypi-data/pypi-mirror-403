from typing import TypeAlias,TypedDict,Any,Callable,Literal
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.webelement import WebElement

LocOrElem: TypeAlias = str | WebElement | None
LocOrElems: TypeAlias = str | list[str] | list[WebElement] | None

WaitTime: TypeAlias = int | float | tuple[int | float, str] | tuple[int | float, int | float, str] | None
IntervalTime: TypeAlias = int | float | list[int | float] | list[int | float | tuple[int | float, str]] | None

LightBhvItem: TypeAlias = tuple[str,str,Any|None]
LightBhvList: TypeAlias = list[LightBhvItem] | None

# all kinds of root element
SearchContext: TypeAlias = WebDriver | WebElement | ShadowRoot
# as element query"s target element
ElementTarget: TypeAlias = str | list[str] | WebElement | list[WebElement]
# as element query"s root element
ElementRoot: TypeAlias = str | SearchContext

# --- ability level ---
AbilityOpts: TypeAlias = TypedDict("AbilityOpts", {
  # value
  "value": Any,

  # locator
  "target": ElementTarget | None,
  "root": ElementRoot | None,
  "draggable": ElementTarget | None,
  "droppable": ElementTarget | None,

  # style 
  "style":str|dict,

  # limit
  "timeout": int|float, # query element"s timeout seconds
  "duration": int|float, # the duration of the action
  "interval": int|float|list[int|float], # a interval value or range 
  
  # switch
  "ephemeral":bool, # use one time and close the window after the ability
})

AbilityDef: TypeAlias = TypedDict("AbilityDef", {
  "name": str,
  "options": AbilityOpts, # SeqOpts
})

# --- seq level ---
SeqHookOpts: TypeAlias = TypedDict("SeqHookOpts", {
  "sleep":int|float, 
  "frame":AbilityOpts, # switch to frame 
  "callback":Callable, # the callback function
})

# support one kind of ability sequence
OrderOpts: TypeAlias = TypedDict("OrderOpts", {
  "name":str, # the ability name
  "children": list[AbilityOpts]|dict[str,AbilityOpts],
  "interval": int|float, # the interval between abilities
})

IntervalValue: TypeAlias = int|float|list[int|float]

LoopOpts: TypeAlias = TypedDict("LoopOpts", {
  "method":str, # only for order
  "target":AbilityOpts, # each / page / next / for by element's target locator
  # for by 
  "count": int, # for by count
  "items": list[dict[str,Any]], # for by items

  "max_attemps": int, # the max loop times, -1 is infinite
  "interval": IntervalValue, # the interval between abilities
})

# ability sequence methods
SeqName: TypeAlias =  Literal["cast" , "cast_order" , "cast_for" , "cast_each" , "cast_page" , "cast_next"]

AbilityCondition: TypeAlias = TypedDict("AbilityCondition", {
  "skip_if": str|bool|int, # skip when the condition is True
  "skip_unless": str|bool|int, # skip when the condition is False
  "break_if": str|bool|int, # break the loop when the condition is True
  "break_unless": str|bool|int, # break the loop when the condition is False
  "throw_if": str|bool|int, # throw an exception when the condition is True
  "throw_unless": str|bool|int, # throw an exception when the condition is False
})

# support all kind of ability sequence
SeqOpts: TypeAlias = TypedDict("SeqOpts", {
  "condition": AbilityCondition, 
  "loop": LoopOpts, # only for items cast
  "children": list[AbilityDef]|dict[str,AbilityDef], 
  
  "before":SeqHookOpts, # do something before cast
  "after":SeqHookOpts, # do something after cast
})

OrderOpts: TypeAlias = TypedDict("OrderOpts", {
  "condition": AbilityCondition, 
  "loop": LoopOpts, # only for items cast
  "children": list[AbilityOpts]|dict[str,AbilityOpts], 
  
  "before":SeqHookOpts, # do something before cast
  "after":SeqHookOpts, # do something after cast
})

SeqDef: TypeAlias = TypedDict("SeqDef", {
  "name": SeqName,
  "options": SeqOpts,
})

# --- plan level ---
DriverStartupOpts: TypeAlias = TypedDict("DriverStartupOpts", {
  "features": list[str],
  "caps": dict[str,Any],
  "arguments": list[str],
  "exp_options": dict[str,Any],
  "extensions": list[str],
  "cdp_cmds": dict[str,Any],
})

# cft: chrome for testing; udc: undetected chrome; udcft: undetected chrome for testing
DriverMode: TypeAlias =  Literal["remote" , "chrome" , "cft" , "udc" , "udcft","context"]

DriverLocOpts: TypeAlias = TypedDict("DriverLocOpts", {
  # for remote
  "command_executor": str,
  # for chrome and udc
  "executable_path": str,
  "binary_location": str,
  # for context
  "path": str,
})

LoginMode: TypeAlias =  Literal["account","sms","qrcode"]
LoginOpts: TypeAlias = TypedDict("LoginOpts", {
  "mode": LoginMode,
  "ephemeral": bool, # whether login once in a session
})
 
DriverDef: TypeAlias = TypedDict("DriverDef", {
  "mode": DriverMode,
  "ephemeral": bool, # whether quit the driver after task finished
  "startup": DriverStartupOpts,
  "location": DriverLocOpts,
  "login": LoginOpts, # need bizdata
})

# --- task level ---

InputMapping: TypeAlias = TypedDict("InputMapping", {
  "source": str,
  "callback": Callable,
  "target": str,
})

InputOpts: TypeAlias = TypedDict("InputOpts", {
  "xcom": list[InputMapping],
  "file": list[InputMapping],
})

TaskType: TypeAlias = Literal["GenericTask","DriverTask","BrowserTask"]

TaskHookOpts: TypeAlias = TypedDict("TaskHookOpts", {
  "switch":AbilityDef, 
  "callback":Callable, # the callback function
})

TaskDef: TypeAlias = TypedDict("TaskDef", {
  # airflow attrs
  "task_id": str,
  "description": str,
  "retries": int,
  "retry_delay_seconds": int,
  
  # user defined attrs
  "type": TaskType,
  "driver": DriverDef,
  "input": InputOpts,
  "abilities": list[AbilityDef|SeqDef]|dict[str,AbilityDef|SeqDef],
  "output":dict,
  
  "before":TaskHookOpts, # do something before cast
  "after":TaskHookOpts, # do something after cast
})

# --- flow level ---
FlowDef: TypeAlias = TypedDict("FlowDef", {
  # airflow attrs
  "dag_id": str,
  "description": str,
  "start_date": list[int],
  "end_date": list[int],
  "schedule": str,
  "catchup": bool,
  
  # user defined attrs
  "tasks": list[TaskDef],
})

FlowBiz: TypeAlias = TypedDict("FlowBiz", {
  "tasks": list[TaskDef],
})
