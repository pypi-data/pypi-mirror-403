from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from instaui.systems.dataclass_system import dataclass
from instaui.internal.ui.app_context import get_current_scope

if TYPE_CHECKING:
    from instaui.internal.ui._scope import Scope


@dataclass(frozen=True)
class JSImport:
    module: str
    members: list[str]


def import_from(module: str, members: list[str], *, scope: Optional[Scope] = None):
    scope = scope or get_current_scope()
    scope.register_import(JSImport(module, members))
