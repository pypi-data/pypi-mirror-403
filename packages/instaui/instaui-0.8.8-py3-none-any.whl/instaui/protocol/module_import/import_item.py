from typing import Optional, Protocol


class PresetProtocol(Protocol):
    module_name: str
    member_name: str
    member_alias: Optional[str] = None
