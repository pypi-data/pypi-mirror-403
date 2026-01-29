from contextvars import copy_context
from typing import Callable, TypeVar

T = TypeVar("T")


class PageExecutionScope:
    """
    Defines the execution boundary of a single page rendering.
    Responsible for isolating ContextVar-based states.
    """

    @staticmethod
    def run(fn: Callable[[], T]) -> T:
        ctx = copy_context()
        return ctx.run(fn)
