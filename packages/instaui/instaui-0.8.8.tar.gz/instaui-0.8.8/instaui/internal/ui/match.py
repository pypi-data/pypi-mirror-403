from typing import Any, Optional
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_container
from instaui.internal.ui.bindable import mark_used
from instaui.internal.ui.renderable import Renderable
from instaui.internal.ui.container import Container


class Match(Renderable):
    def __init__(self, cond: Any):
        """
        Creates a conditional logic container that renders different UI blocks
        based on the value of the given reactive reference. Each case is checked
        sequentially, and the first match will be displayed. A default case can be
        defined to handle unmatched values.

        Args:
            cond (Any): A reactive reference or plain value whose
                state determines which case block should be rendered.

        Example:
        .. code-block:: python
            a = ui.state("")

            html.input().vmodel(a)

            with ui.match(a) as mt:
                with mt.case("page1"):
                    html.paragraph("in page1 case")

                with mt.case("page2"):
                    html.paragraph("in page2 case")

                with mt.default():
                    html.paragraph("in default case")
        """

        super().__init__()
        get_current_container().add_child(self)

        mark_used(cond)
        self._cond = cond
        self._cases: list[MatchCase] = []
        self._default_case: Optional[DefaultCase] = None

    def __enter__(self):
        return MatchWrapper(self)

    def __exit__(self, *_):
        pass


class MatchWrapper:
    def __init__(self, host: Match) -> None:
        self.__host = host

    def case(self, value: Any):
        case = MatchCase(value)
        self.__host._cases.append(case)
        return case

    def default(self):
        default_case = DefaultCase()
        self.__host._default_case = default_case
        return default_case


class MatchCase(Container):
    def __init__(self, value: Any):
        self._value = UILiteralExpr.try_parse(value)
        self._renderables: list[Renderable] = []

    def add_child(self, renderable: Renderable):
        self._renderables.append(renderable)


class DefaultCase(Container):
    def __init__(self):
        self._renderables: list[Renderable] = []

    def add_child(self, renderable: Renderable):
        self._renderables.append(renderable)
