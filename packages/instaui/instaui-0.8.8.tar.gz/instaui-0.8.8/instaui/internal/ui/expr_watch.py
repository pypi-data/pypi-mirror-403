from __future__ import annotations
from typing import (
    Any,
    Optional,
    Sequence,
    Union,
)

from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.bindable import mark_used
from . import watch_types


class ExprWatch:
    def __init__(
        self,
        sources: Union[Any, Sequence],
        code: str,
        *,
        bindings: Optional[dict[str, Any]] = None,
        immediate: bool = False,
        deep: Union[bool, int] = False,
        once: bool = False,
        flush: Optional[watch_types.TFlush] = None,
    ) -> None:
        mark_used(sources)

        self.code = code

        if not isinstance(sources, Sequence):
            sources = [sources]

        self._on = UILiteralExpr.try_parse_list(sources)
        self._bindings = UILiteralExpr.try_parse_dict(bindings) if bindings else None

        self._immediate = immediate
        self._deep = deep
        self._once = once
        self._flush = flush


def expr_watch(
    sources: Union[Any, Sequence],
    code: str,
    *,
    bindings: Optional[dict[str, Any]] = None,
    immediate: bool = False,
    deep: Union[bool, int] = False,
    once: bool = False,
    flush: Optional[watch_types.TFlush] = None,
):
    """ """

    watch = ExprWatch(
        sources,
        code,
        bindings=bindings,
        immediate=immediate,
        deep=deep,
        once=once,
        flush=flush,
    )

    get_current_scope().register_expr_watch(watch)
    return watch
