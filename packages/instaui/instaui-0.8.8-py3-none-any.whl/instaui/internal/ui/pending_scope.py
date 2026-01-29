from instaui.systems.dataclass_system import dataclass


@dataclass
class PendingScope:
    realized: bool = False
