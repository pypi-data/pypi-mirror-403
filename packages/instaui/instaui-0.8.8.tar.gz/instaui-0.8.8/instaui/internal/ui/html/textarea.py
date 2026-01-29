from __future__ import annotations
from typing import Optional, Union
from instaui.internal.ui.element import Element
from instaui.internal.ui.value_element import ValueElement
from instaui.internal.ui.disabled_element import DisabledElement
from ._mixins import InputEventMixin


class Textarea(InputEventMixin, DisabledElement, ValueElement[str]):
    def __init__(
        self,
        value: Union[str, None] = None,
        *,
        model_value: Union[str, None] = None,
        disabled: Optional[bool] = None,
    ):
        super().__init__("textarea", value, is_html_component=True)

        if disabled is not None:
            self.props({"disabled": disabled})
        if model_value is not None:
            self.props({"value": model_value})

    def _input_event_mixin_element(self) -> Element:
        return self
