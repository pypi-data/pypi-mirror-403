from __future__ import annotations
from typing import TYPE_CHECKING

from instaui.internal.ui._scope import Scope
from .container import Container, ScopeGuard
from .slot_prop import SlotProp

if TYPE_CHECKING:
    from .renderable import Renderable


class Slot(Container):
    def __init__(self) -> None:
        super().__init__()
        self.children: list[Renderable] = []
        self._scope_guard = ScopeGuard()
        self._slot_prop = SlotProp()

    def slot_props(self, prop_name: str):
        return self._slot_prop.get(prop_name)

    def add_child(self, child: Renderable):
        self.children.append(child)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def _bind_scope(self, scope: Scope):
        self._scope_guard.bind_scope(scope)

    def _release_scope(self):
        self._scope_guard.release_scope()
