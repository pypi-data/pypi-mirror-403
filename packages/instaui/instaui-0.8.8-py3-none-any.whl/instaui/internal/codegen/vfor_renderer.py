from instaui.internal import import_presets
from instaui.internal.ast.core import (
    VFor,
)
from instaui.internal.ast import expression
from instaui.internal.codegen.base import RenderEmitter
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class VForRenderer:
    def __init__(self, ctx: FileCodegenContext, render_emitter: RenderEmitter) -> None:
        self.ctx = ctx
        self.expr = ExpressionCodegen(ctx)
        self.render_emitter = render_emitter

    def emit(self, vfor: VFor) -> str:
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.vfor())

        array = expression.ObjectExpr.from_kwargs(
            type=vfor.array.type,
            value=vfor.array.value,
        )

        obj = expression.ObjectExpr.from_kwargs(
            fkey=vfor.fkey, array=array, tsGroup=vfor.transition_group
        )

        children_render = self.emit_children(vfor)

        return f"{method}({self.expr.emit(obj)},{self.expr.emit(children_render)})"

    def emit_children(self, vfor: VFor) -> expression.ArrowFunctionExpr:
        if not vfor.children:
            return expression.ArrowFunctionExpr()

        body = [
            expression.RawFunctionExpr(self.render_emitter.emit_render(child))
            for child in vfor.children
        ]

        params = expression.ObjectExpr.from_kwargs(
            i=expression.IdentifierRef(vfor.used_index) if vfor.used_index else None,
            v=expression.IdentifierRef(vfor.used_item) if vfor.used_item else None,
            k=expression.IdentifierRef(vfor.used_key) if vfor.used_key else None,
        )

        return expression.ArrowFunctionExpr(
            params=params, body=expression.ListExpr.from_values(*body)
        )
