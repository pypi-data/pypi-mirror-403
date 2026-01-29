from __future__ import annotations
from typing import Union
from instaui.internal.ui.element import Element
from instaui.internal.ui.components.content import Content
from instaui.internal.ui.vfor import VFor


class Table(Element):
    def __init__(
        self,
        columns: Union[list[str], None] = None,
        rows: Union[list, None] = None,
    ):
        """Create a table element.

        Args:
            columns (Union[list[str], None], optional): A list of column headers or a reactive reference to such a list. Defaults to None.
            rows (Union[list, None], optional): A list of row data, where each row is a list of cell values, or a reactive reference to such a list. Defaults to None.
        """
        super().__init__("table")

        with self:
            with Element("thead"), Element("tr"):
                with VFor(columns) as col:  # type: ignore
                    with Element("th"):
                        Content(col)

            with Element("tbody"):
                with VFor(rows) as row:  # type: ignore
                    with Element("tr"):
                        with VFor(row) as cell:  # type: ignore
                            with Element("td"):
                                Content(cell)
