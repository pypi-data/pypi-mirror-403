from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Optional,
)
from instaui.internal.ui.element import Element
from instaui.internal.ui.event import EventMixin
from instaui.internal.ui.event_modifier import TEventModifier
from instaui.internal.ui.disabled_element import DisabledElement

if TYPE_CHECKING:
    pass


class Button(Element, DisabledElement):
    def __init__(
        self,
        text: Optional[str] = None,
    ):
        super().__init__("button")

        if text is not None:
            self.props(
                {
                    "innerText": text,
                }
            )

    def on_click(
        self,
        handler: EventMixin,
        *,
        params: Optional[list] = None,
        modifier: Optional[list[TEventModifier]] = None,
    ):
        self.on("click", handler, params=params, modifier=modifier)
        return self
