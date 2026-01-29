from typing import Optional
from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class StyleTag:
    content: str
    group_id: Optional[str] = None
