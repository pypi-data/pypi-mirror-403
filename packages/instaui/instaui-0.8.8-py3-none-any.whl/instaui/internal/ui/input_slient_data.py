import typing

from instaui.internal.ui.app_context import get_current_scope

from .bindable import BindableMixin, VarableBindHelper
from .enums import InputBindingType
from .protocol import CanInputProtocol


class InputSilentData(
    BindableMixin,
    CanInputProtocol,
):
    def __init__(self, value: typing.Any) -> None:
        """
        Wraps a value to mark it as "silent" for reactive tracking,
        so that changes to this value do not trigger dependent watchers
        or computed functions.

        Args:
            value (Union[BindingTrackerMixin, Any]): The value to wrap.
                Can be any data type or a reactive binding,
                which will be excluded from triggering reactive updates.


        Example:
        .. code-block:: python
            from instaui import ui, html

            a = ui.state("a")
            b = ui.state("b")
            result = ui.state("result")

            # Use silent data for 'b' so changes to 'b' don't trigger recomputation
            @ui.watch(inputs=[a, ui.slient(b)], outputs=[result])
            def only_a_changed(a: str, b: str):
                return f"{a}+{b}"

            # Only changes to 'a' will update the result
            html.input(a).classes("a")
            html.input(b).classes("b")
            html.paragraph(result)
        """

        self.value = value

        self._bind_helper = VarableBindHelper(
            self,
            define_scope=get_current_scope(),
            lazy_mark_used=[value],
        )

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        pass
