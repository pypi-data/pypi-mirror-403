from instaui.internal import import_presets
from instaui.internal.ast import expression
from instaui.internal.ast.core import ComponentRef
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class ComponentRefRenderer:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self._expr_builder = ExpressionCodegen(ctx)

    def emit(self, component_ref: ComponentRef) -> str:
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.render_scope())

        vfor_options = {}
        if component_ref.vfor:
            if component_ref.vfor.index:
                vfor_options["index"] = expression.ListExpr.from_values(
                    *[
                        expression.ListExpr.from_values(
                            *[
                                expression.Literal(self.ctx.names.resolve(target)),
                                expression.IdentifierRef(target),
                            ]
                        )
                        for target in component_ref.vfor.index
                    ]
                )

            if component_ref.vfor.value:
                vfor_options["value"] = expression.ListExpr.from_values(
                    *[
                        expression.ListExpr.from_values(
                            *[
                                expression.Literal(self.ctx.names.resolve(target)),
                                expression.IdentifierRef(target),
                            ]
                        )
                        for target in component_ref.vfor.value
                    ]
                )

            if component_ref.vfor.item_key:
                vfor_options["itemKey"] = expression.ListExpr.from_values(
                    *[
                        expression.ListExpr.from_values(
                            *[
                                expression.Literal(self.ctx.names.resolve(target)),
                                expression.IdentifierRef(target),
                            ]
                        )
                        for target in component_ref.vfor.item_key
                    ]
                )

        args = [self.ctx.names.resolve(component_ref.id)]
        if vfor_options:
            opt = expression.ObjectExpr.from_dict(
                {"vfor": expression.ObjectExpr.from_dict(vfor_options)}
            )
            args.append(self._expr_builder.emit(opt))

        return f"{method}({', '.join(args)})"
