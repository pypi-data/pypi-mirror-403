from typing import Any, Callable, Optional
from instaui.constants.runtime import RuntimeMode
from instaui.systems.dataclass_system import dataclass


@dataclass()
class RuntimeContext:
    mode: RuntimeMode
    route_path: Optional[str] = None
    debug_mode: bool = False
    request_prefix: str = ""
    meta: Optional[dict] = None
    path_params_getter: Optional[Callable[[str, Any], Any]] = None
