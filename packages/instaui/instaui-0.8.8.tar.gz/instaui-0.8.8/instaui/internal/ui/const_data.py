from __future__ import annotations
from typing import (
    Any,
    TypeVar,
    cast,
)
from instaui.debug.api_boundary import user_api
from instaui.debug.source import get_source_span
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.enums import InputBindingType, OutputSetType
from instaui.internal.ui.variable import Variable
from instaui.internal.ui.bindable import VarableBindHelper, BindableMixin
from instaui.internal.ui.path_var import PathVar
from instaui.internal.ui.protocol import CanInputProtocol, CanOutputProtocol

_T = TypeVar("_T")


class ConstData(Variable, PathVar, CanInputProtocol, CanOutputProtocol, BindableMixin):
    def __init__(self, value: Any = None) -> None:
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        self.value = UILiteralExpr.try_parse(value)
        define_scope = get_current_scope()
        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_data,
            define_scope=define_scope,
            lazy_mark_used=[value],
        )

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    def _to_event_output_type(self) -> OutputSetType:
        raise TypeError("ConstData cannot be used as an output")

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Data

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id


TConstData = ConstData


@user_api
def const_data(value: _T) -> _T:
    return cast(_T, ConstData(value))
