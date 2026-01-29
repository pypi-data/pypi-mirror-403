from typing import Any, Mapping, Optional, Type, TypeVar, cast, overload
from instaui.debug.api_boundary import user_api
from instaui.debug.source import get_source_span
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper
from instaui.internal.ui.enums import InputBindingType
from instaui.internal.ui.path_var import PathVar
from instaui.internal.ui.protocol import ObservableProtocol
from instaui.internal.ui.variable import Variable

_R_TYPE = TypeVar("_R_TYPE")


class ExprComputed(Variable, PathVar, BindableMixin, ObservableProtocol):
    def __init__(
        self,
        code: str,
        bindings: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()
        self.code = code
        self._bindings = UILiteralExpr.try_parse_dict(bindings) if bindings else None

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_expr_computed,
            define_scope=define_scope,
            lazy_mark_used=[self._bindings],
        )

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

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref


TExprComputed = ExprComputed


@overload
def expr_computed(
    code: str,
    *,
    bindings: Optional[Mapping[str, Any]] = None,
) -> Any: ...


@overload
def expr_computed(
    code: str,
    *,
    bindings: Optional[Mapping[str, Any]] = None,
    r_type: Optional[Type[_R_TYPE]] = None,
) -> _R_TYPE: ...


@user_api
def expr_computed(
    code: str,
    *,
    bindings: Optional[Mapping[str, Any]] = None,
    r_type: Optional[Type[_R_TYPE]] = None,
) -> Any | _R_TYPE:
    """
    A client-side computed property that evaluates JavaScript code to derive reactive values.

    Args:
        code (str): JavaScript code to evaluate.
        bindings (Optional[Mapping[str, Any]], optional): Variables to bind to the code. Defaults to None.
        r_type (Optional[Type[_R_TYPE]], optional): Type hint for the return value. Defaults to None.


    """

    computed = ExprComputed(
        code=code,
        bindings=bindings,
    )

    if r_type is None:
        return computed

    return cast(_R_TYPE, computed)
