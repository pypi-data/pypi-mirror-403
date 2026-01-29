from __future__ import annotations
from typing import (
    Generic,
    Optional,
    Union,
    TypeVar,
)
from instaui.internal.ui.element import Element
from instaui.internal.ui.web_computed import WebComputed
from instaui.internal.ui.bindable import mark_used, is_bindable
from instaui.types import TVModelModifier

_T = TypeVar("_T")


class ValueElement(Element, Generic[_T]):
    def __init__(
        self,
        tag: Optional[str] = None,
        value: Union[_T, None] = None,
        is_html_component: bool = False,
        value_name: str = "value",
    ):
        super().__init__(tag)
        self.__is_html_component = is_html_component

        if value is not None:
            if is_bindable(value):
                if isinstance(value, WebComputed):
                    self.props({value_name: value})
                else:
                    self.vmodel(value, prop_name=value_name)
            else:
                self.props({value_name: value})

    def vmodel(
        self,
        value,
        modifiers: Union[TVModelModifier, list[TVModelModifier], None] = None,
        *,
        prop_name: str = "value",
    ):
        mark_used(value)
        return super().vmodel(
            value,
            modifiers,
            prop_name=prop_name,
            is_html_component=self.__is_html_component,
        )
