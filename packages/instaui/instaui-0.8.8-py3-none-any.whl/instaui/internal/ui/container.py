from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional


from .app_context import get_app

if TYPE_CHECKING:
    from .renderable import Renderable
    from instaui.internal.ui._scope import Scope


class Container(ABC):
    @abstractmethod
    def add_child(self, renderable: Renderable): ...

    def __enter__(self):
        get_app().push_container(self)
        return self

    def __exit__(self, *_):
        self._release_scope()
        get_app().pop_container()

    def _bind_scope(self, scope: Scope): ...

    def _release_scope(self): ...


class ScopeGuard:
    def __init__(self):
        self.scope: Optional[Scope] = None

    def release_scope(self):
        if self.scope is None:
            return
        app = get_app()
        app.pop_scope()
        app.pop_container()
        self.scope = None

    def bind_scope(self, scope: Scope):
        self.scope = scope
