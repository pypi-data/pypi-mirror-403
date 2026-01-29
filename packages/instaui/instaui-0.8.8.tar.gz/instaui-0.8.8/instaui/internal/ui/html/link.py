from __future__ import annotations
from typing import (
    Optional,
)
from instaui.internal.ui.element import Element


class Link(Element):
    def __init__(
        self,
        href: Optional[str] = None,
        *,
        text: Optional[str] = None,
    ):
        super().__init__("a")

        if text is not None:
            self.props(
                {
                    "innerText": text,
                }
            )

        if href is not None:
            self.props(
                {
                    "href": href,
                }
            )
