from typing import cast
from typing_extensions import Self
from .element import Element


class DisabledElement:
    def disabled(self, disabled: bool = True) -> Self:
        return cast(Element, self).props({"disabled": disabled})  # type: ignore
