from typing import Optional
from instaui.internal import import_presets
from instaui.internal.ast.core import (
    MatchCase,
    MatchRender,
    Render,
)
from instaui.internal.ast import expression
from instaui.internal.ast.property_key import ExpressionKey
from instaui.internal.codegen.base import RenderEmitter
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class MatchRenderer:
    def __init__(self, ctx: FileCodegenContext, render_emitter: RenderEmitter) -> None:
        self.ctx = ctx
        self.expr = ExpressionCodegen(ctx)
        self.render_emitter = render_emitter

    def emit(self, match: MatchRender) -> str:
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.match())

        cond = match.condition

        opts = expression.ObjectExpr.from_kwargs(
            cs=self.emit_cases(match.cases),
            df=self.emit_default_case(match.default_case),
        )

        return f"{method}({self.expr.emit(cond)},{self.expr.emit(opts)})"

    def emit_cases(self, cases: list[MatchCase]) -> Optional[expression.ObjectExpr]:
        if not cases:
            return None

        return expression.ObjectExpr.from_pairs(
            (
                ExpressionKey(case.value),
                expression.ArrowFunctionExpr(self.parse_renders_body(case.children)),
            )
            for case in cases
        )

    def emit_default_case(
        self, default_case: Optional[list[Render]]
    ) -> Optional[expression.ArrowFunctionExpr]:
        if not default_case:
            return None

        return expression.ArrowFunctionExpr(self.parse_renders_body(default_case))

    def parse_renders_body(self, renders: list[Render]):
        body = [
            expression.RawFunctionExpr(self.render_emitter.emit_render(child))
            for child in renders
        ]

        return expression.ListExpr.from_values(*body)
