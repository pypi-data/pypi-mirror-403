from __future__ import annotations
from typing import Any

from instaui.internal.ui.app_context import get_current_container
from instaui.internal.ui.renderable import Renderable
from instaui.internal.ui.bindable import mark_used


class Content(Renderable):
    def __init__(self, content: Any):
        """Content to be displayed on the page, typically used for pure text content within slots.

        Args:
            content (Any): The textual content to display.

        Examples:
        .. code-block:: python
            with html.div():
                ui.content("Hello, world!")
        """
        mark_used(content)
        self._content = content
        get_current_container().add_child(self)
