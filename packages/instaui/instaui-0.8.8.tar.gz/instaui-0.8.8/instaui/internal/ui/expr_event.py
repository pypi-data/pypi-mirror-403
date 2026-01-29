import typing
from instaui.debug.api_boundary import user_api
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper, mark_used
from instaui.internal.ui.event import EventMixin
from instaui.internal.ui.event_modifier import TEventModifier
from instaui.internal.ui.variable import Variable
from instaui.debug.source import get_source_span


class ExprEvent(Variable, EventMixin, BindableMixin):
    def __init__(
        self,
        *,
        code: str,
        bindings: typing.Optional[dict[str, typing.Any]] = None,
    ):
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()
        self._code = code
        self._bindings = UILiteralExpr.try_parse_dict(bindings or {})

        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_expr_event,
            define_scope=define_scope,
            lazy_mark_used=[self._bindings],
        )

    def _attach_to_element(
        self,
        *,
        params: typing.Optional[typing.Sequence],
        modifier: typing.Optional[typing.Sequence[TEventModifier]],
    ):
        mark_used(params)
        mark_used(modifier)
        self._mark_used()

        return self

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


@user_api
def expr_event(
    *,
    code: str,
    bindings: typing.Optional[dict[str, typing.Any]] = None,
):
    """
    Create an event object that can be bound to a UI component's event listener.

    This function generates a callable event handler with optional contextual bindings.
    The event logic is defined via a code string, which can reference bound variables.

    Args:
        code (str): A string containing the executable logic for the event handler.
                    Typically contains a function body or expression that utilizes bound variables.
        bindings (typing.Optional[dict[str, typing.Any]], optional): A dictionary mapping variable names to values that should be available in the
            event handler's context. If None, no additional bindings are created.. Defaults to None.

    Example:
    .. code-block:: python
        a = ui.state(1)

        event = ui.vue_event(bindings={"a": a}, code=r'''()=> { a.value +=1}''')

        html.span(a)
        html.button("plus").on("click", event)
    """
    return ExprEvent(code=code, bindings=bindings)
