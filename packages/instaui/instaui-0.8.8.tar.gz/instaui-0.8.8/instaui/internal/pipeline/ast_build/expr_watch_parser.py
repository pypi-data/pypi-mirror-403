from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.ui._scope import Scope
from instaui.internal.ast import core as ast_core, expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui.expr_watch import ExprWatch

if TYPE_CHECKING:
    pass


class ExprWatchParser:
    def __init__(
        self,
        builder_ctx: AstBuilderContext,
    ) -> None:
        self.ctx = builder_ctx
        self.expr = ExprBuilder(builder_ctx)

    def parse(self, scope: Scope) -> Optional[list[ast_core.ExprWatchCall]]:
        if not scope._expr_watchs:
            return None

        return [self._parse_watch(watch) for watch in scope._expr_watchs]

    def _parse_watch(self, watch: ExprWatch):
        args = expression.ObjectExpr.from_kwargs(
            code=expression.Literal(watch.code),
            on=self.expr.list_shallow(watch._on),
            bind=self.expr.object_shallow(watch._bindings) if watch._bindings else None,
            immediate=expression.Literal(watch._immediate)
            if watch._immediate
            else None,
            deep=expression.Literal(watch._deep) if watch._deep else None,
            once=expression.Literal(watch._once) if watch._once else None,
            flush=expression.Literal(watch._flush) if watch._flush else None,
        )

        return ast_core.ExprWatchCall(args)
