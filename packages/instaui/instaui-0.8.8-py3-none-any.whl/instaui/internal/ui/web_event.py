from typing import Callable, Generic, Hashable, Optional, Sequence, TypeVar, overload
from typing_extensions import ParamSpec
from instaui.debug.api_boundary import user_api
from instaui.debug.model import SourceSpan
from instaui.debug.source import get_source_span
from instaui.internal.codec import build_type_adapter_map
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.event_context import DatasetEventContext
from instaui.internal.ui.pre_setup import normalize_pre_setup
from instaui.internal.ui.utils.func_utils import extract_defaults_and_strip
from instaui.protocol.invocation.spec import EventSpec

from .variable import Variable
from .event_modifier import TEventModifier
from .app_context import get_app, get_current_scope
from .event import EventMixin
from .utils.validators import ensure_output_list
from .bindable import BindableMixin, VarableBindHelper, mark_used
from .web_event_param import is_event_param

P = ParamSpec("P")
R = TypeVar("R")


class WebEvent(EventMixin, BindableMixin, Variable, Generic[P, R]):
    def __init__(
        self,
        fn: Callable[P, R],
        inputs: Sequence,
        outputs: Sequence,
        pre_setup: list | None = None,
        modifier: Sequence[TEventModifier] | None = None,
        *,
        extra_key: Optional[Sequence[Hashable]] = None,
        _source_span_: SourceSpan,
    ):
        self._source_span_ = _source_span_
        new_scope_if_needed()
        ensure_output_list(outputs)
        define_scope = get_current_scope()

        if not inputs:
            default_params, fn = extract_defaults_and_strip(fn)
            inputs = [x.default for x in default_params]

        inputs = [input for input in inputs if not is_event_param(input)]

        self._inputs = UILiteralExpr.try_parse_list(inputs)
        self._outputs = outputs
        self._fn = fn
        self._pre_setup = normalize_pre_setup(pre_setup or [])
        self._modifier = modifier or []
        self._extra_key = extra_key

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_web_event,
            define_scope=define_scope,
            lazy_mark_used=[
                *self._inputs,
                *self._outputs,
                *[x[0] for x in self._pre_setup],
            ],
        )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._fn(*args, **kwargs)

    def _attach_to_element(
        self,
        *,
        params: Sequence | None = None,
        modifier: Sequence[TEventModifier] | None = None,
    ):
        mark_used(params)
        mark_used(self)

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

    def _export_invocation_spec(self) -> EventSpec:
        type_adapter_map = build_type_adapter_map(self._fn, self._inputs)
        dataset_input_indexs = [
            i
            for i, input_ in enumerate(self._inputs or [])
            if isinstance(input_, DatasetEventContext)
        ]
        return EventSpec(
            len(self._outputs or []),
            dataset_input_indexs,
            type_adapter_map,
            extra_key=self._extra_key,
        )


@overload
def event(_func: Callable[P, R]) -> WebEvent[P, R]: ...


@overload
def event(
    *,
    inputs: Sequence | None = ...,
    outputs: Sequence | None = ...,
    pre_setup: list | None = ...,
    extra_key: Sequence[Hashable] | None = ...,
) -> Callable[[Callable[P, R]], WebEvent[P, R]]: ...


@user_api
def event(
    _func: Callable[P, R] | None = None,
    *,
    inputs: Sequence | None = None,
    outputs: Sequence | None = None,
    pre_setup: list | None = None,
    extra_key: Sequence[Hashable] | None = None,
) -> WebEvent[P, R] | Callable[[Callable[P, R]], WebEvent[P, R]]:
    """
    Creates an event handler decorator for binding reactive logic to component events.

    Args:
        inputs (Optional[Sequence], optional): Reactive sources (state objects, computed properties)
                                   that should be accessible during event handling.
                                   These values will be passed to the decorated function
                                   when the event fires.
        outputs (Optional[Sequence], optional): Targets (state variables, UI elements) that should
                                    update when this handler executes. Used for coordinating
                                    interface updates after the event is processed.
        pre_setup (Optional[list], optional): A list of pre-setup actions to be executed before the event executes.


    # Example:
    .. code-block:: python
        from instaui import ui, html

        a = ui.state(0)

        @ui.event(inputs=[a], outputs=[a])
        def plus_one(a):
            return a + 1

        html.button("click me").on_click(plus_one)
        html.paragraph(a)

    use pre_setup:
    .. code-block:: python
        a = ui.state(0)
        task_running = ui.state(False)

        @ui.event(inputs=[a], outputs=[a], pre_setup=[task_running,True,False])
        async def long_running_task(a):
            await asyncio.sleep(3)
            return a + 1

        html.button("click me").on_click(long_running_task).disabled(task_running)
    """

    if get_app().mode == "zero":
        raise Exception(
            "Cannot use event decorator in zero mode. You should use `ui.js_event` instead."
        )

    _source_span_ = get_source_span()

    def decorator(func: Callable[P, R]):
        return WebEvent(
            func,
            inputs or [],
            outputs=outputs or [],
            pre_setup=pre_setup,
            extra_key=extra_key,
            _source_span_=_source_span_,
        )

    # case：@event
    if _func is not None and callable(_func):
        return decorator(_func)

    # case：@event(...)
    return decorator
