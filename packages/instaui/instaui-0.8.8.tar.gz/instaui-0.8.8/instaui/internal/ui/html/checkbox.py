from __future__ import annotations
from typing import (
    Any,
    Optional,
    Union,
)

from instaui.internal.ui.element import Element
from instaui.internal.ui.value_element import ValueElement
from ._mixins import InputEventMixin


class Checkbox(InputEventMixin, ValueElement[bool | str | list]):
    def __init__(
        self,
        value: bool | str | list | None = None,
        *,
        model_value: Union[bool, str, None] = None,
        checked: Optional[bool] = None,
        id: Optional[Any] = None,
    ):
        super().__init__("input", value, is_html_component=True)
        self.props({"type": "checkbox"})
        if id is not None:
            self.props({"id": id})
        if checked is not None:
            self.props({"checked": checked})
        if model_value is not None:
            self.props({"value": model_value})

    def _input_event_mixin_element(self) -> Element:
        return self
