from instaui.debug.api_boundary import user_api
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper
from instaui.internal.ui.enums import InputBindingType
from instaui.internal.ui.protocol import CanInputProtocol
from instaui.internal.ui.variable import Variable
from instaui.debug.source import get_source_span


class JsFn(
    Variable,
    CanInputProtocol,
    BindableMixin,
):
    def __init__(self, code: str, *, execute_immediately=False):
        self._source_span_ = get_source_span()
        new_scope_if_needed()

        self.code = code
        self._execute_immediately = execute_immediately

        define_scope = get_current_scope()
        self._bind_helper = VarableBindHelper(
            self, define_scope.register_js_fn, define_scope=define_scope
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
        return InputBindingType.JsFn


@user_api
def js_fn(code: str, *, execute_immediately=False):
    """
    Creates a JavaScript function object from a raw code string.
    Valid targets include: `js_computed`, `js_watch`, and similar JS-bound methods.

    Args:
        code (str): Valid JavaScript function definition string.

    Example:
    .. code-block:: python
        a = ui.state(1)
        add = ui.js_fn(code="(a,b)=> a+b ")
        result = ui.js_computed(inputs=[add, a], code="(add,a)=>  add(a,10) ")

        html.number(a)
        ui.text(result)
    """

    return JsFn(code, execute_immediately=execute_immediately)
