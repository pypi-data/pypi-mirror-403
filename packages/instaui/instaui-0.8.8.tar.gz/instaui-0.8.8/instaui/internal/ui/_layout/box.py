from __future__ import annotations
from typing import Optional, Literal
from typing_extensions import Unpack
from instaui.internal.ui.element import Element
from .base_props import TLayoutBaseProps
from instaui.internal.ui.components._responsive_type._common import TMaybeResponsive


class Box(Element):
    def __init__(
        self,
        *,
        as_: Optional[Literal["div", "span"]] = None,
        as_child: Optional[bool] = None,
        display: Optional[
            TMaybeResponsive[Literal["none", "inline-block", "block", "contents"]]
        ] = None,
        **kwargs: Unpack[TLayoutBaseProps],
    ):
        """
        Creates a flexible box container with responsive layout properties.

        Args:
            as_ (Optional[Literal["div", "span"]]): HTML element type to render as.
            as_child (Optional[bool]): Whether to merge props with parent component.
            display (Optional[TMaybeResponsive[Literal["none", "inline-block", "block", "contents"]]]):
                CSS display property for the box.
            **kwargs (Unpack[TLayoutBaseProps]): Additional layout properties like padding, margin, etc.

        Example:
        .. code-block:: python
            # Basic box with padding
            with ui.box(p="1"):
                ui.text("Content")

            # Box with as_child to merge with parent
            with ui.box(p="1", as_child=True):
                ui.text("Merged content")

            # Responsive box with different padding per breakpoint
            with ui.box(
                p={"initial": "1px", "sm": "2", "md": "3", "lg": "4", "xl": "5"}
            ):
                ui.text("Responsive content")

            # Box with reactive padding
            padding = ui.state("1")
            with ui.box(p=padding):
                ui.text("Dynamic padding")
        """
        super().__init__("box")

        self.props(
            {
                "as": as_,
                "as_child": as_child,
                "display": display,
                **kwargs,
            }
        )
