import contextvars
from contextlib import contextmanager
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)

_IN_PAGE = contextvars.ContextVar("_IN_PAGE", default=False)

_PAGE_EXIT_CALLBACKS: contextvars.ContextVar[list[Callable[[], None]] | None] = (
    contextvars.ContextVar("_PAGE_EXIT_CALLBACKS", default=None)
)


def in_page_context() -> bool:
    """Returns whether currently in the execution context of page()"""
    return _IN_PAGE.get()


def on_page_exit(callback: Callable[[], Any]) -> None:
    """
    Register a callback to be invoked when exiting the current page context.

    Must be called inside a page context.
    """
    if not in_page_context():
        raise RuntimeError(
            "on_page_exit() must be called inside a page() execution context"
        )

    callbacks = _PAGE_EXIT_CALLBACKS.get()
    if callbacks is None:
        raise RuntimeError("Page exit callback storage is not initialized")

    callbacks.append(callback)


@contextmanager
def enter_page_context():
    """
    Enters the page context.
    The page() decorator should call this context manager before invoking the user function.
    """
    token = _IN_PAGE.set(True)
    cb_token = _PAGE_EXIT_CALLBACKS.set([])
    try:
        yield
    finally:
        callbacks = _PAGE_EXIT_CALLBACKS.get() or []
        for cb in callbacks:
            try:
                cb()
            except Exception:
                logger.exception("Error in page exit callback")

        _PAGE_EXIT_CALLBACKS.reset(cb_token)
        _IN_PAGE.reset(token)
