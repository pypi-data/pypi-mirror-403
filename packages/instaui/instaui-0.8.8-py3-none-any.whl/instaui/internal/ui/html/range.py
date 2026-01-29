from __future__ import annotations
from typing import Union
from instaui.internal.ui.element import Element
from instaui.internal.ui.value_element import ValueElement
from instaui.internal.ui.bindable import BindableMixin
from instaui.types import TVModelModifier
from ._mixins import InputEventMixin

_T_value = Union[int, float]


class Range(InputEventMixin, ValueElement[_T_value]):
    def __init__(
        self,
        value: Union[_T_value, None] = None,
        *,
        min: Union[_T_value, None] = None,
        max: Union[_T_value, None] = None,
        step: Union[_T_value, None] = None,
    ):
        super().__init__("input", value, is_html_component=True)
        self.props({"type": "range"})

        if min is not None:
            self.props({"min": min})
        if max is not None:
            self.props({"max": max})
        if step is not None:
            self.props({"step": step})

    def vmodel(
        self,
        value: BindableMixin,
        modifiers: Union[TVModelModifier, list[TVModelModifier], None] = None,
        *,
        prop_name: str = "value",
    ):
        modifiers = modifiers or []
        if isinstance(modifiers, str):
            modifiers = [modifiers]

        modifiers_with_number = list(set([*modifiers, "number"]))

        return super().vmodel(value, modifiers_with_number, prop_name=prop_name)  # type: ignore

    def _input_event_mixin_element(self) -> Element:
        return self
