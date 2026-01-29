from __future__ import annotations
import typing
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


_R_TYPE = typing.TypeVar("_R_TYPE")


class JsComputed(Variable, PathVar, BindableMixin, ObservableProtocol):
    def __init__(
        self,
        *,
        inputs: typing.Optional[typing.Sequence] = None,
        code: str,
        async_init_value: typing.Optional[typing.Any] = None,
        deep_compare_on_input: bool = False,
        tool: typing.Optional[typing.Literal["unwrap_reactive"]] = None,
    ) -> None:
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()
        self.code = code
        self._inputs = UILiteralExpr.try_parse_list(inputs or [])

        self._async_init_value = UILiteralExpr.try_parse(async_init_value)
        self._deep_compare_on_input = deep_compare_on_input
        self._tool = tool

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_js_computed,
            define_scope=define_scope,
            lazy_mark_used=self._inputs,
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


TJsComputed = JsComputed


@typing.overload
def js_computed(
    *,
    inputs: typing.Optional[typing.Sequence] = None,
    code: str,
    async_init_value: typing.Optional[typing.Any] = None,
    deep_compare_on_input: bool = False,
) -> typing.Any: ...


@typing.overload
def js_computed(
    *,
    inputs: typing.Optional[typing.Sequence] = None,
    code: str,
    async_init_value: typing.Optional[typing.Any] = None,
    deep_compare_on_input: bool = False,
    r_type: typing.Optional[typing.Type[_R_TYPE]] = None,
) -> _R_TYPE: ...


@user_api
def js_computed(
    *,
    inputs: typing.Optional[typing.Sequence] = None,
    code: str,
    async_init_value: typing.Optional[typing.Any] = None,
    deep_compare_on_input: bool = False,
    r_type: typing.Optional[typing.Type[_R_TYPE]] = None,
) -> typing.Union[JsComputed, _R_TYPE]:
    """
    A client-side computed property that evaluates JavaScript code to derive reactive values.

    Args:
        inputs (typing.Optional[typing.Sequence], optional): Reactive data sources to monitor.
                                                  Changes to these values trigger re-computation.
        code (str): JavaScript code to execute for computing the value.
        async_init_value (typing.Optional[typing.Any], optional): Initial value to use before first successful async evaluation.

    # Example:
    .. code-block:: python
        a = ui.state(0)

        plus_one = ui.js_computed(inputs=[a], code="a=> a+1")

        html.number(a)
        ui.text(plus_one)
    """

    jc = JsComputed(
        inputs=inputs,
        code=code,
        async_init_value=async_init_value,
        deep_compare_on_input=deep_compare_on_input,
    )

    if r_type is None:
        return jc

    return typing.cast(_R_TYPE, jc)
