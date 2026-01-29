from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, ClassVar, Optional

from instaui.constants.runtime import RuntimeMode

if TYPE_CHECKING:
    from instaui.internal.ui._scope import Scope
    from instaui.internal.ui.pending_scope import PendingScope
    from instaui.internal.ui.container import Container
    from instaui.internal.ui.layout import Layout


class App:
    _default_app: ClassVar[Optional[App]] = None

    def __init__(
        self,
        mode: RuntimeMode,
        *,
        debug: bool,
        meta: Optional[dict] = None,
    ) -> None:
        super().__init__()
        self._scoped_style_id_counter = 0
        self._scope_id_counter = 0
        self._container_stack: list[Container] = []
        self._scope_stack: list[Scope] = []
        self._pending_scope_stack: list[PendingScope] = []
        self._created_scopes: list[Scope] = []
        self._mode: RuntimeMode = mode
        self._debug_mode: bool = debug
        self.meta = meta

        self._used_icons: set[str] = set()
        self._used_icons_set: set[str] = set()
        self.layouts: list[Layout] = []
        self._page_once_registry: set[str] = set()

    @property
    def created_scopes(self):
        return self._created_scopes

    def next_scope_id(self) -> int:
        self._scope_id_counter += 1
        return self._scope_id_counter

    def append_layout(self, layout: Layout) -> None:
        self.layouts.append(layout)

    def push_scope(self, scope: Scope):
        self._scope_stack.append(scope)
        self._created_scopes.append(scope)

    def pop_scope(self) -> Scope:
        return self._scope_stack.pop()

    def push_pending_scope(self, pending_scope: PendingScope):
        self._pending_scope_stack.append(pending_scope)

    def pop_pending_scope(self) -> PendingScope:
        return self._pending_scope_stack.pop()

    def has_pending_scope(self) -> bool:
        return len(self._pending_scope_stack) > 0

    def top_pending_scope(self):
        return self._pending_scope_stack[-1]

    def push_container(self, container: Container):
        self._container_stack.append(container)

    def pop_container(self) -> Container:
        return self._container_stack.pop()

    def get_current_scope(self) -> Scope:
        assert len(self._scope_stack) > 0, "Scope stack is empty"
        return self._scope_stack[-1]

    def get_current_container(self) -> Container:
        assert len(self._container_stack) > 0, "Container stack is empty"
        return self._container_stack[-1]

    def collect_icon(self, icon_name: str):
        self._used_icons.add(icon_name)

    def collect_icon_set(self, icon_set_name: str):
        self._used_icons_set.add(icon_set_name)

    @contextmanager
    def _mark_router_base_scope(self, scope: Scope):
        self._router_base_scope = scope
        yield
        self._router_base_scope = None

    @property
    def router_base_scope(self):
        return self._router_base_scope

    @property
    def mode(self) -> RuntimeMode:
        return self._mode

    @property
    def debug_mode(self) -> bool:
        return self._debug_mode

    def gen_scoped_style_group_id(self):
        gid = f"scoped-style-{self._scoped_style_id_counter}"
        self._scoped_style_id_counter += 1
        return gid


class DefaultApp(App):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DefaultApp, cls).__new__(cls)
        return cls._instance

    def new_scope(self):
        raise ValueError("Operations are not allowed outside of ui.page")


App._default_app = DefaultApp(mode=RuntimeMode.WEB, debug=False)
