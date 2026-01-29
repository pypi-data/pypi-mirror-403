from __future__ import annotations
from typing import (
    Generator,
    Literal,
    Optional,
    Tuple,
    Union,
    Sequence,
    Generic,
    TypeVar,
    cast,
)
from contextlib import contextmanager
from enum import Enum
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.pending_scope import PendingScope
from instaui.systems.dataclass_system import dataclass
from instaui.internal.ui._scope import Scope
from instaui.internal.ui.app_context import get_app, get_current_container
from instaui.internal.ui.renderable import Renderable, ScopeBoundaryRenderable
from instaui.internal.ui.bindable import is_bindable, mark_used
from instaui.internal.ui.container import Container, ScopeGuard
from instaui.internal.ui.vfor_item import VForItem, VForIndex, VForItemKey

_T = TypeVar("_T")


@dataclass()
class _VForRangeInfo:
    end: int
    start: int = 1
    step: int = 1

    def mark_used(self):
        mark_used(self.end)
        mark_used(self.start)
        mark_used(self.step)

    def to_dict(self):
        return {
            "end": self.end,
            "start": self.start if self.start != 1 else None,
            "step": self.step if self.step != 1 else None,
        }


class VForArrayTypeEnum(Enum):
    CONST = "c"
    REF = "r"
    RANGE = "n"


class VFor(ScopeBoundaryRenderable, Container, Generic[_T]):
    def __init__(
        self,
        data: Union[Sequence[_T], dict[str, _T], _T, None],
        *,
        key: Union[Literal["item", "index"], str] = "index",
        range: Optional[_VForRangeInfo] = None,
    ):
        """for loop component.

        Args:
            data (Union[Sequence[_T], ElementBindingMixin[list[_T]]]): data source.
            key (Union[Literal[&quot;item&quot;, &quot;index&quot;], str]]): key for each item. Defaults to 'index'.

        Examples:
        .. code-block:: python
            items = ui.state([1,2,3])

            with ui.vfor(items) as item:
                html.span(item)

            # object key
            items = ui.state([{"name": "Alice"}, {"name": "Bob"}])
            with ui.vfor(items, key="item.name") as item:
                html.span(item.name)

            # js computed key
            items = ui.state([{"name": "Alice"}, {"name": "Bob"}])
            with ui.vfor(items, key=": (item , index) => item.name + index") as item:
                html.span(item.name)

            # iter info
            items = ui.state({"a": 1, "b": 2, "c": 3})
            with ui.vfor(items).with_key() as [value, key]:

                html.span(key)
                html.span(value)

            # range
            with ui.vfor.range(10) as i:
                html.paragraph(i)
        """

        super().__init__()
        get_current_container().add_child(self)

        if is_bindable(data):
            self._array_type = VForArrayTypeEnum.REF
        else:
            self._array_type = VForArrayTypeEnum.CONST

        if range is not None:
            assert data is None, "range and data cannot be used together"
            self._array_type = VForArrayTypeEnum.RANGE
            mark_used(range.to_dict())

        mark_used(data)
        self._data = UILiteralExpr.try_parse(data) if data is not None else None
        self._range = range.to_dict() if range else None
        self._key = key
        self._transition_group_setting = None

        self._vfor_item = VForItem()
        self._vfor_index = VForIndex()
        self._vfor_item_key = VForItemKey()
        self._renderables: list[Renderable] = []
        self._scope_guard = ScopeGuard()

    def __enter__(self) -> _T:
        super().__enter__()
        get_app().push_pending_scope(PendingScope())
        return cast(_T, self._vfor_item)

    def __exit__(self, *_):
        get_app().pop_pending_scope()
        super().__exit__(*_)

    @contextmanager
    def with_index(self) -> Generator[Tuple[_T, int], None, None]:
        with self:
            yield (
                self._vfor_item,
                self._vfor_index,
            )  # type: ignore

    @contextmanager
    def with_key(self) -> Generator[Tuple[_T, str], None, None]:
        with self:
            yield (self._vfor_item, self._vfor_item_key)  # type: ignore

    @contextmanager
    def with_key_index(self) -> Generator[Tuple[_T, str, int], None, None]:
        with self:
            yield (
                self._vfor_item,
                self._vfor_item_key,
                self._vfor_index,
            )  # type: ignore

    def _set_range_type(self):
        self._array_type = VForArrayTypeEnum.RANGE

    def transition_group(self, name="fade", tag: Optional[str] = None):
        self._transition_group_setting = {"name": name, "tag": tag}
        return self

    @classmethod
    def range(
        cls,
        end: int,
        *,
        start: int = 0,
        step: int = 1,
    ) -> VFor[int]:
        obj = cls(None, range=_VForRangeInfo(start=start, end=end, step=step))

        return obj  # type: ignore

    def add_child(self, renderable: Renderable):
        self._renderables.append(renderable)

    def _bind_scope(self, scope: Scope):
        self._scope_guard.bind_scope(scope)

    def _release_scope(self):
        self._scope_guard.release_scope()
