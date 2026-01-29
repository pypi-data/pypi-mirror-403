import typing

from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.bindable import mark_used
from instaui.internal.ui.utils.bindings_utils import auto_made_inputs_to_slient
from instaui.internal.ui.utils.validators import ensure_output_list
from . import watch_types


class JsWatch:
    def __init__(
        self,
        code: str,
        inputs: typing.Optional[typing.Sequence] = None,
        outputs: typing.Optional[typing.Sequence] = None,
        immediate: bool = True,
        deep: typing.Union[bool, int] = False,
        once: bool = False,
        flush: typing.Optional[watch_types.TFlush] = None,
    ) -> None:
        ensure_output_list(outputs)
        self.code = code

        inputs = auto_made_inputs_to_slient(list(inputs or []), list(outputs or []))

        self._inputs = UILiteralExpr.try_parse_list(inputs or [])
        self._outputs = outputs

        self._immediate = immediate
        self._deep = deep
        self._once = once
        self._flush = flush

        mark_used(self._inputs)
        mark_used(self._outputs)


def js_watch(
    *,
    inputs: typing.Optional[typing.Sequence] = None,
    outputs: typing.Optional[typing.Sequence] = None,
    code: str,
    immediate: bool = True,
    deep: typing.Union[bool, int] = True,
    once: bool = False,
    flush: typing.Optional[watch_types.TFlush] = None,
):
    """
    Creates a client-side observer that executes JavaScript code in response to reactive source changes.

    Args:
        inputs (typing.Optional[typing.Sequence], optional): Reactive sources to observe. Changes to these sources
                                   trigger the watcher's JavaScript execution.
        outputs (typing.Optional[typing.Sequence], optional): Output targets associated with this watcher. Used for
                                    coordination with other observers.
        code (str, optional): JavaScript code to execute when changes are detected. The code has access
                  to the current values of observed inputs through the `args` parameter.
        immediate (bool, optional):If True, executes the watcher immediately after creation with current values. Defaults to True.
        deep (typing.Union[bool, int], optional): Controls depth of change detection:
                               - True: Recursively tracks nested properties
                               - False: Shallow comparison only
                               - int: Maximum depth level to track (for complex objects).
                               Defaults to True.
        once (bool, optional): If True, automatically stops observation after first trigger. Defaults to False.
        flush (typing.Optional[_types.TFlush], optional): Controls when to flush updates:
                                      - 'sync': Execute immediately on change
                                      - 'post': Batch updates and execute after current tick
                                      - 'pre': Execute before render phase (if applicable)

    # Example:
    .. code-block:: python
        from instaui import ui, html

        num = ui.state(0)
        msg = ui.state('')
        ui.js_watch(inputs=[num], outputs=[msg], code="num => `The number is ${num}`")

        html.number(num)
        ui.text(msg)
    """

    watch = JsWatch(code, inputs, outputs, immediate, deep, once, flush)
    get_current_scope().register_js_watch(watch)
    return watch
