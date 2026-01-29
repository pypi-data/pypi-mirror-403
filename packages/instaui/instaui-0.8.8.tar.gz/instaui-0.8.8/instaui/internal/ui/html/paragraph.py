from __future__ import annotations
from typing import Any, Union
from instaui.internal.ui.element import Element


class Paragraph(Element):
    """
    A component class representing an HTML `<p>` (paragraph) element.

    Args:
        text (Union[str, TMaybeRef[Any]]):The text content of the paragraph.
                                          - If a string is provided, the content is static.
                                          - If a `TMaybeRef` object is provided, the content
                                            will reactively update when the referenced value changes.
    """

    def __init__(
        self,
        text: Union[str, Any],
    ):
        super().__init__("p")
        self.props(
            {
                "innerText": text,
            }
        )
