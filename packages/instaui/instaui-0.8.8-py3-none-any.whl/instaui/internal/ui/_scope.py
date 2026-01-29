from __future__ import annotations
from typing import TYPE_CHECKING

from instaui.internal.ui.app_context import get_app


from .variable import Variable
from .container import Container, ScopeGuard
from .renderable import Renderable

if TYPE_CHECKING:
    from instaui.internal.ui.ref_base import RefBase
    from instaui.internal.ui.custom_var import CustomVar
    from instaui.internal.ui.const_data import ConstData
    from instaui.internal.ui.web_computed import WebComputed
    from instaui.internal.ui.js_computed import JsComputed

    from instaui.internal.ui.expr_computed import ExprComputed
    from instaui.internal.ui.web_watch import WebWatch
    from instaui.internal.ui.js_watch import JsWatch
    from instaui.internal.ui.expr_watch import ExprWatch

    from instaui.internal.ui.element_ref import ElementRef
    from instaui.internal.ui.web_event import WebEvent
    from instaui.internal.ui.js_event import JsEvent
    from instaui.internal.ui.expr_event import ExprEvent
    from instaui.internal.ui.imports import JSImport
    from instaui.internal.ui.js_fn import JsFn


class Scope(Container, Renderable):
    def __init__(self) -> None:
        super().__init__()

        self._id = get_app().next_scope_id()

        self._refs: list[RefBase] = []
        self._custom_refs: list[CustomVar] = []
        self._web_computeds: list[WebComputed] = []
        self._js_computeds: list[JsComputed] = []
        self._element_refs: list[ElementRef] = []
        self._expr_computeds: list[ExprComputed] = []
        self._run_method_records: list = []
        self._web_watchs: list[WebWatch] = []
        self._js_watchs: list[JsWatch] = []
        self._expr_watchs: list[ExprWatch] = []
        self._web_events: list[WebEvent] = []
        self._js_events: list[JsEvent] = []
        self._expr_events: list[ExprEvent] = []
        self._js_fns: list[JsFn] = []
        self._js_imports: list[JSImport] = []

        self.variable_order: list[Variable] = []
        self._renderables: list[Renderable] = []
        self._scope_guard = ScopeGuard()
        self._injected: set[Variable] = set()
        self._provided: set[Variable] = set()

    @property
    def id(self) -> int:
        return self._id

    def __enter__(self):
        app = get_app()
        app.push_scope(self)
        return super().__enter__()

    def __exit__(self, *_):
        get_app().pop_scope()
        return super().__exit__(*_)

    def inject(self, variable: Variable):
        self._injected.add(variable)

    def provide(self, variable: Variable):
        self._provided.add(variable)

    def register_import(self, js_import: JSImport):
        self._js_imports.append(js_import)

    def register_data(self, data: ConstData):
        self.variable_order.append(data)

    def register_custom_ref(self, ref: CustomVar):
        self._custom_refs.append(ref)
        self.variable_order.append(ref)

    def register_ref(self, ref: RefBase):
        self._refs.append(ref)
        self.variable_order.append(ref)

    def register_element_ref(self, ref: ElementRef):
        self._element_refs.append(ref)
        self.variable_order.append(ref)

    def register_js_computed(self, computed: JsComputed):
        self._js_computeds.append(computed)
        self.variable_order.append(computed)

    def register_expr_computed(self, computed: ExprComputed):
        self._expr_computeds.append(computed)
        self.variable_order.append(computed)

    def register_web_computed(self, web_computed: WebComputed):
        self._web_computeds.append(web_computed)
        self.variable_order.append(web_computed)

    def register_web_watch(self, web_watch: WebWatch):
        self._web_watchs.append(web_watch)

    def register_js_watch(self, js_watch: JsWatch):
        self._js_watchs.append(js_watch)

    def register_expr_watch(self, vue_watch: ExprWatch):
        self._expr_watchs.append(vue_watch)

    def register_web_event(self, event: WebEvent):
        self._web_events.append(event)
        self.variable_order.append(event)

    def register_js_event(self, event: JsEvent):
        self._js_events.append(event)
        self.variable_order.append(event)

    def register_expr_event(self, event: ExprEvent):
        self._expr_events.append(event)
        self.variable_order.append(event)

    def register_js_fn(self, fn: JsFn):
        self._js_fns.append(fn)
        self.variable_order.append(fn)

    def add_child(self, renderable: Renderable):
        self._renderables.append(renderable)

    def _bind_scope(self, scope: Scope):
        self._scope_guard.bind_scope(scope)

    def _release_scope(self):
        self._scope_guard.release_scope()
