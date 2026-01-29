from typing import TypeVar, cast
from pydantic import BaseModel

from instaui.internal.ui._expr.codec_expr import DataCodecExpr
from instaui.internal.ui.path_var import PathTrackerBindable
from instaui.internal.ui.to_value import ToValue
from instaui.protocol.ui.state import StateReadable
from instaui.debug.api_boundary import user_api

from .bindable import BindableMixin
from .ref_base import RefBase

_T = TypeVar("_T")


class StateModel(BaseModel):
    pass


@user_api
def state(value: _T, deep_compare: bool = False) -> _T:
    """
    Creates a reactive state wrapper that enables automatic UI updates when its value or
    nested elements change. Supports primitives, lists, dictionaries, and provides
    reactive operations such as indexing, comparisons, and length evaluation.

    Args:
        value (_T): The initial value to be wrapped as a reactive state. Can be any
            Python type including primitives, lists, or dictionaries.
        deep_compare (bool): Whether state updates should compare nested values to
            determine change propagation. Defaults to False.

    Example:
    .. code-block:: python
        from instaui import ui, html

        # Value reactivity
        s = ui.state('hello')
        html.input(s)
        ui.text(s)


        # List reactivity
        items = ui.state([1, 2, 3])
        html.number(items[0])
        html.ul.from_list(items)


        # Dictionary mutation triggers UI updates
        data = ui.state({"name": "John"})
        html.input(data["name"])


        # State used with js_computed
        data = ui.state({"items": [1, 2, 3]})
        items = ui.js_computed(inputs=[data], code="(d)=> d.items")
        html.ul.from_list(items)


        # Boolean operations maintain reactivity
        value = ui.state([{"state": True}])
        html.checkbox(value[0]["state"])
        html.paragraph(ui.not_(value[0]["state"]))


        # String or list length as reactive value
        text = ui.state("Hello")
        html.paragraph(ui.str_format("len: {}", ui.len_(text)))


        # Comparison operators trigger updates
        a = ui.state(1)
        b = ui.state(2)
        html.paragraph(a < b)  # UI updates when a or b changes
    """

    if isinstance(value, RefBase):
        return value

    if isinstance(value, StateReadable) or _readable_source_of_path_tracker(value):
        value = cast(_T, ToValue(value))

    new_value = value if isinstance(value, (BindableMixin)) else DataCodecExpr(value)

    return cast(_T, RefBase(value=new_value, deep_compare=deep_compare))


def _readable_source_of_path_tracker(value):
    return isinstance(value, PathTrackerBindable) and isinstance(
        value._source, StateReadable
    )
