from __future__ import annotations
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Sequence,
    TypeVar,
    cast,
    overload,
)
from typing_extensions import ParamSpec
from collections.abc import Hashable
from instaui.debug.api_boundary import user_api
from instaui.debug.model import SourceSpan
from instaui.debug.source import get_source_span
from instaui.internal.codec import build_type_adapter_map
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.protocol import ObservableProtocol
from instaui.internal.ui.utils.bindings_utils import auto_made_inputs_to_slient
from instaui.internal.ui.utils.func_utils import extract_defaults_and_strip
from instaui.protocol.invocation.spec import ComputedSpec

from .variable import Variable
from .bindable import BindableMixin, VarableBindHelper
from .app_context import get_app, get_current_scope
from .app_index import new_scope_if_needed
from .enums import InputBindingType
from .path_var import PathVar
from .pre_setup import normalize_pre_setup


P = ParamSpec("P")
R = TypeVar("R")


class WebComputed(
    PathVar,
    BindableMixin,
    Variable,
    ObservableProtocol,
    Generic[P, R],
):
    def __init__(
        self,
        func: Callable[P, R],
        inputs: Optional[Sequence] = None,
        extend_outputs: Optional[Sequence] = None,
        init_value: Optional[R] = None,
        evaluating: Optional[Any] = None,
        deep_compare_on_input: bool = False,
        pre_setup: Optional[list] = None,
        debug_info: Optional[dict] = None,
        extra_key: Optional[Sequence[Hashable]] = None,
        *,
        _source_span_: SourceSpan,
    ) -> None:
        self._source_span_ = _source_span_
        new_scope_if_needed()
        define_scope = get_current_scope()
        self._pre_setup = normalize_pre_setup(pre_setup or [])

        if not inputs:
            default_params, func = extract_defaults_and_strip(func)
            inputs = [x.default for x in default_params]

        inputs = auto_made_inputs_to_slient(
            list(inputs), [self, *(extend_outputs or [])]
        )

        self._inputs = UILiteralExpr.try_parse_list(inputs or [])
        self._extend_outputs = extend_outputs or []

        self._fn = func
        self._init_value = UILiteralExpr.try_parse(init_value)
        self._deep_compare_on_input = deep_compare_on_input

        if evaluating is not None:
            self._pre_setup.append([evaluating, True, False])

        if debug_info is not None:
            self.debug = debug_info

        self._extra_key = extra_key

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_web_computed,
            define_scope=define_scope,
            lazy_mark_used=[
                *self._inputs,
                *(extend_outputs or []),
                *[x[0] for x in self._pre_setup],
            ],
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

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._fn(*args, **kwargs)

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _export_invocation_spec(self) -> ComputedSpec:
        type_adapter_map = build_type_adapter_map(self._fn, self._inputs)

        return ComputedSpec(
            len(self._extend_outputs) + 1,
            custom_type_adapter_map=type_adapter_map,
            extra_key=self._extra_key,
        )


@overload
def web_computed(_func: Callable[P, R]) -> R: ...


@overload
def web_computed(
    *,
    inputs: Optional[Sequence] = ...,
    extend_outputs: Optional[Sequence] = ...,
    init_value: Optional[Any] = ...,
    evaluating: Optional[Any] = ...,
    deep_compare_on_input: bool = ...,
    pre_setup: Optional[list] = ...,
    extra_key: Optional[Sequence[Hashable]] = ...,
    debug_info: Optional[dict] = ...,
) -> Callable[[Callable[P, R]], R]: ...


@user_api
def web_computed(
    _func: Optional[Callable[P, R]] = None,
    *,
    inputs: Optional[Sequence] = None,
    extend_outputs: Optional[Sequence] = None,
    init_value: Optional[Any] = None,
    evaluating: Optional[Any] = None,
    deep_compare_on_input: bool = False,
    pre_setup: Optional[list] = None,
    extra_key: Optional[Sequence[Hashable]] = None,
    debug_info: Optional[dict] = None,
):
    """
    Creates a computed property decorator for reactive programming with dependency tracking.

    This decorator factory wraps functions to create reactive computed properties that:
    - Automatically re-evaluate when dependencies (inputs) change
    - Cache results for performance optimization
    - Support both synchronous and asynchronous computation patterns

    Args:
        inputs (Optional[Sequence], optional): Collection of reactive sources that trigger recomputation
                                   when changed. These can be state objects or other computed properties.
        extend_outputs (Optional[Sequence], optional):  Additional outputs to notify when this computed value updates.
        init_value (Optional[Any], optional): Initial value to return before first successful evaluation.
        evaluating (Optional[Any], optional): Temporary value returned during asynchronous computation.
        pre_setup (typing.Optional[list], optional): A list of pre-setup actions to be executed before the event executes.

    # Example:
    .. code-block:: python
        from instaui import ui,html

        a = ui.state(0)

        @ui.computed(inputs=[a])
        def plus_one(a):
            return a + 1

        html.number(a)
        ui.text(plus_one)
    """

    if get_app().mode == "zero":
        raise Exception(
            "Cannot use computed decorator in zero mode. You should use `ui.js_computed` instead."
        )

    _source_span_ = get_source_span()

    def decorator(func: Callable[P, R]):
        return cast(
            R,
            WebComputed(
                func,
                inputs=inputs,
                extend_outputs=extend_outputs,
                init_value=init_value,
                evaluating=evaluating,
                deep_compare_on_input=deep_compare_on_input,
                pre_setup=pre_setup,
                debug_info=debug_info,
                extra_key=extra_key,
                _source_span_=_source_span_,
            ),
        )

    # case：@computed
    if _func is not None and callable(_func):
        return decorator(_func)

    # case：@computed(...)
    return decorator


TComputed = WebComputed
