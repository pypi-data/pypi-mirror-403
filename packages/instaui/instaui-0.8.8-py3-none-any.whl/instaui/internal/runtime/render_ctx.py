from typing import Optional
from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class RenderContext:
    app_meta: dict
    route: Optional[str] = None
