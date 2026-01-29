from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class ComponentRegistry:
    name: str
    url: str
