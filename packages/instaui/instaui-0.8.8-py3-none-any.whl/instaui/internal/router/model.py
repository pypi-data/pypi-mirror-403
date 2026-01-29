from typing import Callable
from instaui.systems.dataclass_system import dataclass


@dataclass()
class PageInfo:
    fn: Callable
    cache: bool = True
