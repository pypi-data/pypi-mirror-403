from __future__ import annotations
from typing import Any, Optional, Literal, Union
from instaui.internal.ui.element import Element
from ._responsive_type._common import (
    TMaybeResponsive,
    TLevel_1_9,
)
from ._responsive_type._typography import (
    TWeightEnum,
    TTextWrapEnum,
    TTrimEnum,
    TAlignEnum,
)


class Text(Element):
    def __init__(
        self,
        text: Optional[Any] = None,
        *,
        as_: Optional[Literal["span", "div", "label", "p", "pre"]] = None,
        as_child: Optional[bool] = None,
        size: Optional[TMaybeResponsive[TLevel_1_9]] = None,
        weight: Optional[TMaybeResponsive[Union[TWeightEnum, str]]] = None,
        align: Optional[TMaybeResponsive[Union[TAlignEnum, str]]] = None,
        trim: Optional[Union[TTrimEnum, str]] = None,
        truncate: Optional[bool] = None,
        text_wrap: Optional[Union[TTextWrapEnum, str]] = None,
    ):
        """
        Creates a text element with customizable styling and typography options.

        Args:
            text (Optional[Any]]: The text content to display.
            as_ (Optional[Literal["span", "div", "label", "p", "pre"]]]):
                HTML element type to render as. Defaults to appropriate semantic element.
            as_child (Optional[bool]): Whether to merge props with parent component.
            size (Optional[TMaybeResponsive[TLevel_1_9]]): Text size level from 1 to 9.
            weight (Optional[TMaybeResponsive[Union[TWeightEnum, str]]): Font weight.
            align (Optional[TMaybeResponsive[Union[TAlignEnum, str]]): Text alignment.
            trim (Optional[Union[TTrimEnum, str]]): Whitespace trimming behavior.
            truncate (Optional[bool]): Whether to truncate overflowing text.
            text_wrap (Optional[Union[TTextWrapEnum, str]]): Text wrapping behavior.

        Example:
        .. code-block:: python
            # Basic text element
            ui.text("ui.text")

            # Text with specific HTML element and styling
            ui.text(
                "Styled text",
                as_="div",
                size=3,
                weight="bold",
                align="center"
            )
        """
        super().__init__("ui-text")

        self.props(
            {
                "innerText": text,
                "as": as_,
                "as_child": as_child,
                "size": size,
                "weight": weight,
                "text_align": align,
                "trim": trim,
                "truncate": truncate,
                "text_wrap": text_wrap,
            }
        )
