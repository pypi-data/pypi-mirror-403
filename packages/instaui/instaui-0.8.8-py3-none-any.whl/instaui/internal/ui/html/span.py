from __future__ import annotations
from typing import Any, Union
from instaui.internal.ui.element import Element


class Span(Element):
    def __init__(
        self,
        text: Union[str, Any],
    ):
        super().__init__("span")
        self.props(
            {
                "innerText": text,
            }
        )
