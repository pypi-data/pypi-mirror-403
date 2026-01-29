from instaui.internal.ui.app_context import get_current_container
from instaui.internal.ui.bindable import mark_used
from instaui.internal.ui.renderable import Renderable
from instaui.internal.ui.container import Container


class VIf(Renderable, Container):
    def __init__(self, on: bool | int | str):
        """
        A conditional container that renders its children only when the given condition is True.

        Args:
            on (bool | int | str): A boolean or reactive reference that determines whether the container's
                                child elements should be displayed. If True, children are rendered;
                                if False, children are hidden.


        Example:
        .. code-block:: python
            from instaui import ui, html

            value = ui.state(False)

            html.button("toggle").on_click(
                ui.js_event(inputs=[value], outputs=[value], code="(v)=> !v")
            )

            with ui.vif(value):
                ui.text("show")
        """

        super().__init__()
        get_current_container().add_child(self)

        mark_used(on)
        self._on = on
        self._renderables: list[Renderable] = []

    def add_child(self, renderable: Renderable):
        self._renderables.append(renderable)
