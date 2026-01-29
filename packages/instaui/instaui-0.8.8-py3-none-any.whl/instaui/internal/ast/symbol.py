from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class SymbolId:
    """
    The "name" at the logical level
    - Variables
    - Components
    - Module members
    """

    uid: int
