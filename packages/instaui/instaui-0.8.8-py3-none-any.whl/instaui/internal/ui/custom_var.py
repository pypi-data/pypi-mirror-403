from __future__ import annotations
from typing import Any, Callable, Optional

from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui._expr.maybe_ref_expr import UIMaybeRefExpr
from instaui.internal.ui.imports import import_from
from instaui.internal.ui.protocol import CanOutputProtocol, ObservableProtocol
from instaui.protocol.ui.state import StateReadable
from instaui.systems.dataclass_system import dataclass
from instaui.debug.source import get_source_span
from .app_index import new_scope_if_needed
from .variable import Variable
from .enums import InputBindingType, OutputSetType
from .path_var import PathVar
from .bindable import BindableMixin, VarableBindHelper
from .app_context import get_current_scope


@dataclass(frozen=True)
class CustomRefMethod:
    module_name: str
    method_name: str


class CustomVar(
    PathVar,
    Variable,
    ObservableProtocol,
    CanOutputProtocol,
    BindableMixin,
):
    def __init__(
        self,
        module: str,
        method: str,
        *,
        args: Optional[Any] = None,
        deep_compare: bool = False,
        on_mark_used_fn: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        self._define_scope = get_current_scope()

        def on_register_fn():
            import_from(module, [method])
            if on_mark_used_fn:
                on_mark_used_fn()

        self._bind_helper = VarableBindHelper(
            self,
            self._define_scope.register_custom_ref,
            define_scope=self._define_scope,
            on_register_fn=on_register_fn,
            lazy_mark_used=[args],
        )

        self._method = CustomRefMethod(module, method)
        self._deep_compare = deep_compare
        self._args = _build_args(args)

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.Ref

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id

    @staticmethod
    def maybe_ref(value: Any):
        return UIMaybeRefExpr(value)

    @staticmethod
    def literal(value: Any):
        return UILiteralExpr(value)


class StateReadableCustomVar(CustomVar, StateReadable):
    pass


def _build_args(args):
    match args:
        case tuple():
            return tuple(UILiteralExpr.try_parse(arg) for arg in args)

        case list():
            return UILiteralExpr.try_parse_list(args)

        case dict():
            return UILiteralExpr.try_parse_dict(args)
        case None:
            return None
        case _:
            return UILiteralExpr.try_parse(args)
