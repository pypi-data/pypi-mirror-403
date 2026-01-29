from __future__ import annotations
from typing import Any, Union
from instaui.internal.ui.element import Element


class Li(Element):
    def __init__(
        self,
        text: Union[Any, None] = None,
    ):
        super().__init__("li")

        if text:
            self.props({"innerText": text})
