from typing import Any
from instaui.systems.dataclass_system import dataclass, field


@dataclass()
class JsExpr:
    code: str


@dataclass(frozen=True)
class ReprKey:
    value: Any = field(hash=True)
