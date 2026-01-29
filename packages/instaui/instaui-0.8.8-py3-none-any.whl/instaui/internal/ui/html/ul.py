from __future__ import annotations
from typing import Sequence
from instaui.internal.ui.element import Element
from .li import Li
from instaui.internal.ui.vfor import VFor


class Ul(Element):
    def __init__(self):
        super().__init__("ul")

    @classmethod
    def from_list(cls, data: Sequence) -> Ul:
        with Ul() as ul:
            with VFor(data) as items:
                Li(items)

        return ul
