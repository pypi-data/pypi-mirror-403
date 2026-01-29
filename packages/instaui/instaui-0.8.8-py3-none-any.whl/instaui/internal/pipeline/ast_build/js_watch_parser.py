from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.pipeline.ast_build.utils import ui_bindings_utils

from instaui.internal.ui._scope import Scope
from instaui.internal.ast import core as ast_core, expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui.js_watch import JsWatch

if TYPE_CHECKING:
    pass


class JsWatchParser:
    def __init__(
        self,
        builder_ctx: AstBuilderContext,
    ) -> None:
        self.ctx = builder_ctx
        self.expr = ExprBuilder(builder_ctx)

    def parse(self, scope: Scope) -> Optional[list[ast_core.JsWatchCall]]:
        if not scope._js_watchs:
            return None

        return [self._parse_js_watch(watch) for watch in scope._js_watchs]

    def _parse_js_watch(self, watch: JsWatch):
        outputs = list(watch._outputs or [])
        inputs, slients, _ = ui_bindings_utils.analyze_observable_inputs(watch._inputs)
        slients = ui_bindings_utils.normalize_int_values(slients)

        output_types = ui_bindings_utils.normalize_int_values(
            [x._to_event_output_type().value for x in outputs]
        )

        args = expression.ObjectExpr.from_kwargs(
            code=expression.Literal(watch.code),
            inputs=self.expr.list_expr(mode="literal", values=inputs)
            if inputs
            else None,
            outputs=self.expr.list_expr(mode="literal", values=outputs)
            if outputs
            else None,
            opTypes=expression.ListLiteral(list(output_types))
            if output_types
            else None,
            slient=expression.ListLiteral(list(slients)) if slients else None,
            immediate=None
            if watch._immediate
            else expression.Literal(watch._immediate),
            deep=None if watch._deep else expression.Literal(watch._deep),
            once=expression.Literal(watch._once) if watch._once else None,
            flush=expression.Literal(watch._flush) if watch._flush else None,
        )

        return ast_core.JsWatchCall(args)
