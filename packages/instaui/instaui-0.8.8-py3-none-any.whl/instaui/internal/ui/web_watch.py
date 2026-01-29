from __future__ import annotations
from collections.abc import Hashable
from typing import Any, TypeVar, Callable, Generic, Optional, Sequence, Union
from typing_extensions import ParamSpec
from instaui.debug.api_boundary import user_api
from instaui.debug.model import SourceSpan
from instaui.debug.source import get_source_span
from instaui.internal.codec import build_type_adapter_map
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.pre_setup import normalize_pre_setup
from instaui.internal.ui.utils.bindings_utils import auto_made_inputs_to_slient
from instaui.internal.ui.utils.func_utils import extract_defaults_and_strip
from instaui.internal.ui.utils.validators import ensure_output_list
from instaui.protocol.invocation.spec import WatchSpec

from .bindable import mark_used
from .app_context import get_app, get_current_scope
from . import watch_types


P = ParamSpec("P")
R = TypeVar("R")


class WebWatch(Generic[P, R]):
    def __init__(
        self,
        func: Callable[P, R],
        inputs: Optional[Sequence] = None,
        outputs: Optional[Sequence] = None,
        immediate: bool = True,
        deep: Union[bool, int] = True,
        once: bool = False,
        flush: Optional[watch_types.TFlush] = None,
        pre_setup: Optional[list] = None,
        _debug: Optional[Any] = None,
        extra_key: Optional[Sequence[Hashable]] = None,
        *,
        _source_span_: SourceSpan,
    ) -> None:
        self._source_span_ = _source_span_
        ensure_output_list(outputs)

        if not inputs:
            default_params, func = extract_defaults_and_strip(func)
            inputs = [x.default for x in default_params]

        inputs = auto_made_inputs_to_slient(list(inputs), list(outputs or []))

        self._inputs = UILiteralExpr.try_parse_list(inputs or [])
        self._outputs = outputs

        self._fn = func
        self._immediate = immediate
        self._deep = deep
        self._once = once
        self._flush = flush
        self._debug = _debug
        self._pre_setup = normalize_pre_setup(pre_setup or [])
        self._extra_key = extra_key

        mark_used(self._inputs)
        mark_used(self._outputs)
        mark_used([x[0] for x in self._pre_setup or []])

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._fn(*args, **kwargs)

    def _export_invocation_spec(self) -> WatchSpec:
        type_adapter_map = build_type_adapter_map(self._fn, self._inputs)
        return WatchSpec(
            len(self._outputs or []), type_adapter_map, extra_key=self._extra_key
        )


@user_api
def watch(
    _func: Optional[Callable] = None,
    *,
    inputs: Optional[Sequence] = None,
    outputs: Optional[Sequence] = None,
    immediate: bool = True,
    deep: Union[bool, int] = True,
    once: bool = False,
    flush: Optional[watch_types.TFlush] = None,
    pre_setup: Optional[list] = None,
    extra_key: Optional[Sequence[Hashable]] = None,
    _debug: Optional[Any] = None,
):
    """
    Creates an observer that tracks changes in reactive sources and triggers callbacks.

    Args:
        inputs (Optional[Sequence], optional): Reactive sources to observe (state objects or computed properties).
                                   Changes to these sources trigger the watcher callback.
        outputs (Optional[Sequence], optional): Output targets associated with this watcher.
                                    Used for coordination with computed properties or other observers.
        immediate (bool, optional): If True, executes callback immediately after creation with current values. Defaults to True.
        deep (Union[bool, int], optional): Controls depth of change detection:
                               - True: Recursively tracks nested properties
                               - False: Shallow comparison only
                               - int: Maximum depth level to track (for complex objects).
                               Defaults to True.
        once (bool, optional):  If True, automatically stops observation after first trigger. Defaults to False.
        flush (Optional[watch_types.TFlush], optional): Controls when to flush updates:
                                      - 'sync': Execute immediately on change
                                      - 'post': Batch updates and execute after current tick
                                      - 'pre': Execute before render phase (if applicable)
        pre_setup (Optional[list], optional): A list of pre-setup actions to be executed before the event executes.


    # Example:
    .. code-block:: python
        from instaui import ui, html

        num = ui.state(0)
        msg = ui.state('')

        @ui.watch(inputs=[num], outputs=[msg])
        def when_num_change(num):
            return f"The number is {num}"

        html.number(num)
        ui.text(msg)

    list append:
    .. code-block:: python
        from instaui import ui, html

        num = ui.state(0)
        msg = ui.state([])

        @ui.watch(inputs=[num, msg], outputs=[msg])
        def when_num_change(num, msg:list):
            msg.append(f"The number changed to {num}")
            return msg

        html.number(num)
        ui.text(msg)

    """
    app = get_app()
    if app.mode == "zero":
        raise Exception(
            "Cannot use watch decorator in zero mode. You should use `ui.js_watch` instead."
        )

    _source_span_ = get_source_span()

    def decorator(func: Callable[P, R]):
        obj = WebWatch(
            func,
            inputs,
            outputs=outputs,
            immediate=immediate,
            deep=deep,
            once=once,
            flush=flush,
            pre_setup=pre_setup,
            _debug=_debug,
            extra_key=extra_key,
            _source_span_=_source_span_,
        )

        get_current_scope().register_web_watch(obj)

        return func

    # case：@watch
    if _func is not None and callable(_func):
        return decorator(_func)

    # case：@watch(...)
    return decorator
