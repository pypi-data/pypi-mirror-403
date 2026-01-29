from typing import Callable, Generator, Optional, Union, overload
from instaui.internal.context.page_context import in_page_context
from instaui.internal.ui.app_context import get_default_app


TLayoutFn = Callable[[], Generator[None, None, None]]


class Layout:
    def __init__(self, fn: TLayoutFn, priority: int = 0) -> None:
        self.fn = fn
        self.priority = priority

    def create_generator(self) -> Generator[None, None, None]:
        return self.fn()


@overload
def layout(fn: TLayoutFn) -> TLayoutFn: ...


@overload
def layout(*, priority: int) -> Callable[[TLayoutFn], TLayoutFn]: ...


def layout(
    fn: Optional[TLayoutFn] = None, *, priority: int = 0
) -> Union[TLayoutFn, Callable[[TLayoutFn], TLayoutFn]]:
    """
    Define a global page layout.

    The decorated function MUST be a generator function
    and MUST yield exactly once.
    """

    def decorator(fn: TLayoutFn) -> TLayoutFn:
        assert not in_page_context(), (
            "layout() should be called outside ui.page() context"
        )
        app = get_default_app()
        app.append_layout(Layout(fn, priority=priority))
        return fn

    if fn is None:
        return decorator
    else:
        return decorator(fn)


def clear_layout():
    assert not in_page_context(), (
        "remove_layout() should be called outside ui.page() context"
    )
    app = get_default_app()
    app.layouts.clear()
