from __future__ import annotations
from instaui.internal.ui.element import Element


class Label(Element):
    def __init__(
        self,
        text: str,
        *,
        for_: str | int | None = None,
    ):
        super().__init__("label")

        self.props(
            {
                "for": for_,
                "innerText": text,
            }
        )
