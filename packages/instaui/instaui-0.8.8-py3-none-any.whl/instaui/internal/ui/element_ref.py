from instaui.debug.source import get_source_span
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.app_index import new_scope_if_needed
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper
from instaui.internal.ui.enums import InputBindingType, OutputSetType
from instaui.internal.ui.protocol import CanOutputProtocol, ObservableProtocol
from instaui.internal.ui.variable import Variable


class ElementRef(
    Variable,
    ObservableProtocol,
    CanOutputProtocol,
    BindableMixin,
):
    def __init__(self) -> None:
        """
        A reference holder for a frontend DOM element, enabling two-way interaction between
        Python and JavaScript. The referenced element can be used as input/output in JS
        events, and methods can be executed dynamically on the element at runtime.

        Args:
            None: The reference is created without initialization parameters. It will be
                bound to an element using ``element_ref(...)`` during UI construction.

        Example:
        .. code-block:: python
            # 1️ Use ElementRef inside ui.event as an output
            cp = ui.element_ref()

            @ui.event(outputs=[cp])
            def on_click():
                return ui.run_element_method("reset")

            Counter("my counter").element_ref(cp)
            html.button("reset").on_click(on_click)


            # 2️⃣ Use ElementRef as input to ui.js_event
            ele = ui.element_ref()
            click_event = ui.js_event(inputs=[ele], code="(ele)=> ele.increment()")

            CounterWithRefInput().element_ref(ele)
            html.button("click").on_click(click_event)


            # 3️⃣ Access DOM element inside JavaScript event using `ele.$el ?? ele`
            ele_dom = ui.element_ref()
            output = ui.state("")

            ui.text("custom").element_ref(ele_dom).on(
                "click",
                ui.js_event(
                    inputs=[ele_dom],
                    outputs=[output],
                    code="ele => (ele.$el ?? ele).tagName"
                ),
            )
            ui.text(output)
        """
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()
        self._bind_helper = VarableBindHelper(
            self, define_scope.register_element_ref, define_scope=define_scope
        )

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.ElementRefAction

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.ElementRef


def run_element_method(method_name: str, *args, **kwargs):
    return {
        "method": method_name,
        "args": args,
    }
