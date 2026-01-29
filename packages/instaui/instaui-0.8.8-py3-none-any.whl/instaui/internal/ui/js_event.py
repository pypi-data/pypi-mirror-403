import typing
from instaui.debug.api_boundary import user_api
from instaui.debug.source import get_source_span
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper, mark_used
from instaui.internal.ui.event import EventMixin
from instaui.internal.ui.event_modifier import TEventModifier
from instaui.internal.ui.variable import Variable


class JsEvent(Variable, EventMixin, BindableMixin):
    def __init__(
        self,
        code: str,
        inputs: typing.Optional[typing.Sequence] = None,
        outputs: typing.Optional[typing.Sequence] = None,
    ):
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()

        self._inputs = UILiteralExpr.try_parse_list(inputs or [])
        self._outputs = outputs or []
        self._code = code

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_js_event,
            define_scope=define_scope,
            lazy_mark_used=[*self._inputs, *(outputs or [])],
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

    def _attach_to_element(
        self,
        *,
        params: typing.Optional[typing.Sequence],
        modifier: typing.Optional[typing.Sequence[TEventModifier]] = None,
    ):
        mark_used(params)
        mark_used(modifier)
        self._mark_used()

        return self


@user_api
def js_event(
    *,
    inputs: typing.Optional[typing.Sequence] = None,
    outputs: typing.Optional[typing.Sequence] = None,
    code: str,
):
    """
    Creates a client-side event handler decorator for binding JavaScript logic to UI component events.

    Args:
        inputs (typing.Optional[typing.Sequence], optional):Reactive sources (state variables, computed values)
                                   that should be passed to the event handler. These values
                                   will be available in the JavaScript context through the `args` array.
        outputs (typing.Optional[typing.Sequence], optional): Targets (state variables, UI elements) that should
                                    update when this handler executes. Used for coordinating
                                    interface updates after the event is processed.
        code (str): JavaScript code to execute when the event is triggered.

    # Example:
    .. code-block:: python
        from instaui import ui, html

        a = ui.state(0)

        plus_one = ui.js_event(inputs=[a], outputs=[a], code="a =>a + 1")

        html.button("click me").on_click(plus_one)
        html.paragraph(a)

    """
    return JsEvent(inputs=inputs, outputs=outputs, code=code)
