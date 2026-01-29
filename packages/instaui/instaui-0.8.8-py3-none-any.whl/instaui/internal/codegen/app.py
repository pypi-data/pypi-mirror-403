from instaui.internal.ast.core import App
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen
from .component_codegen import ComponentCodegen


class AppCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.names = ctx.names
        self.import_table = ctx.imports
        self.bindings = ctx.root.binding_registry
        self.app_bootstrap_codegen = ctx.root.components.app_bootstrap_codegen_factory(
            ctx
        )
        self.expr_codegen = ExpressionCodegen(ctx)

    def emit(self, app: App) -> str:
        component_codegen = ComponentCodegen(self.ctx)

        parts: list[str] = []

        # component name registry
        for comp in app.components:
            self.names.declare_component(comp.id)

        # components
        for comp in app.components:
            parts.append(component_codegen.emit(comp))

        parts.append(self.app_bootstrap_codegen.emit(app.bootstrap))

        body = "\n\n".join(parts)
        return f"{self.import_table.render()}\n\n{body}"
