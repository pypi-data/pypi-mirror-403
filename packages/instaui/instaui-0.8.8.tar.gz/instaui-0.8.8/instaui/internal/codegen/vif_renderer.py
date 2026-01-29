from instaui.internal import import_presets
from instaui.internal.ast.core import (
    VIf,
)
from instaui.internal.ast import expression
from instaui.internal.codegen.base import RenderEmitter
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class VIfRenderer:
    def __init__(self, ctx: FileCodegenContext, render_emitter: RenderEmitter) -> None:
        self.ctx = ctx
        self.expr = ExpressionCodegen(ctx)
        self.render_emitter = render_emitter

    def emit(self, vif: VIf) -> str:
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.vif())

        children_render = self.emit_children(vif)
        opts = expression.ObjectExpr.from_kwargs(on=vif.condition)
        return f"{method}({self.expr.emit(opts)},{self.expr.emit(children_render)})"

    def emit_children(self, vif: VIf) -> expression.ArrowFunctionExpr:
        if not vif.children:
            return expression.ArrowFunctionExpr()

        body = [
            expression.RawFunctionExpr(self.render_emitter.emit_render(child))
            for child in vif.children
        ]

        return expression.ArrowFunctionExpr(body=expression.ListExpr.from_values(*body))
