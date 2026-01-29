from instaui.internal import import_presets
from instaui.internal.ast.core import AppBootstrap, CustomComponent, Plugin
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class AppBootstrapCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.import_table = ctx.imports
        self.expr = ExpressionCodegen(ctx)

    def emit(self, bootstrap: AppBootstrap) -> str:
        method = self.import_table.use_from_preset(import_presets.Instaui.install())
        self.ctx.names.declare_top_level_var(bootstrap.target)

        app_var = self.ctx.names.resolve(bootstrap.target)

        parts: list[str] = []
        parts.append(self.parse_app_def(app_var, method, bootstrap))

        if bootstrap.custom_components:
            parts.append(
                self._emit_custom_components(app_var, bootstrap.custom_components)
            )

        if bootstrap.plugins:
            parts.append(self._emit_plugins(app_var, bootstrap.plugins))

        return "\n".join(parts)

    def parse_app_def(self, app_var: str, method: str, bootstrap: AppBootstrap) -> str:
        return f"const {app_var} = {method}({self.ctx.names.resolve(bootstrap.root.id)},{self.expr.emit(bootstrap.meta)})"

    def _emit_plugins(self, app_var: str, plugins: list[Plugin]) -> str:
        parts: list[str] = []
        for plugin in plugins:
            parts.append(self._emit_plugin(app_var, plugin))
        return "\n".join(parts)

    def _emit_plugin(self, app_var: str, plugin: Plugin) -> str:
        args = self.expr.emit(plugin.options) if plugin.options else ""
        return f"{app_var}.use((await import({self.expr.emit(plugin.url)})),{args})"

    def _emit_custom_components(
        self, app_var: str, custom_components: list[CustomComponent]
    ) -> str:
        parts: list[str] = []
        for custom_component in custom_components:
            parts.append(self._emit_custom_component(app_var, custom_component))
        return "\n".join(parts)

    def _emit_custom_component(
        self, app_var: str, custom_component: CustomComponent
    ) -> str:
        return f"{app_var}.component({self.expr.emit(custom_component.name)},(await import({self.expr.emit(custom_component.url)})).default)"
