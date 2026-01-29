from typing import Optional

from instaui.systems.dataclass_system import dataclass
from .event_modifier import TEventModifier
from .event import EventMixin


@dataclass()
class EventArgs:
    name: str
    event: EventMixin
    params: Optional[list] = None
    modifier: Optional[list[TEventModifier]] = None
