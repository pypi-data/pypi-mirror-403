from instaui.internal import import_presets
from instaui.internal.ast.core import ComponentDef, ExprWatchCall, JsWatchCall
from instaui.internal.ast import expression
from instaui.internal.ast.symbol import SymbolId
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen
from instaui.internal.codegen.render_codegen import RenderCodegen
from instaui.internal.codegen.variable_decl_codegen import VariableDeclCodegen
from instaui.internal.codegen.web_watch_task import WebWatchTaskRenderer


class ComponentCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.import_table = ctx.imports
        self.bindings = ctx.root.binding_registry
        self.expr = ExpressionCodegen(ctx)
        self.var_decl = VariableDeclCodegen(ctx)
        self._web_watch_task = WebWatchTaskRenderer(ctx)

    def emit(self, comp: ComponentDef) -> str:
        # declare variables
        for var in comp.vars:
            self.ctx.names.declare_var(var)

        name = self.ctx.names.resolve(comp.id)

        parts: list[str] = []

        # setup
        setup_lines: list[str] = []

        # injects
        if comp.injects:
            setup_lines.append(self.emit_injects(comp.injects))

        # variables
        setup_lines.extend(self.var_decl.emit(var) for var in comp.variables)

        # web watch tasks
        if comp.web_watch_tasks:
            setup_lines.append(self._web_watch_task.emit(comp.web_watch_tasks))

        # js watch
        if comp.js_watchs:
            setup_lines.append(self.emit_js_watch_call(comp.js_watchs))

        # expr watch
        if comp.expr_watchs:
            setup_lines.append(self.emit_expr_watch_call(comp.expr_watchs))

        if comp.on_mounted_calls:
            mounted_method = self.import_table.use_from_preset(
                import_presets.Vue.on_mounted()
            )
            setup_lines.extend(
                [
                    f"{mounted_method}(() => {{",
                    "\n    ".join(
                        self.expr.emit(call) for call in comp.on_mounted_calls
                    ),
                    "});",
                ]
            )

        # provide
        if comp.provides:
            setup_lines.append(self.emit_provides(comp.provides))

        # render
        render_codegen = RenderCodegen(self.ctx)
        render_code = render_codegen.emit_renders(comp.renders)

        setup_body = "\n    ".join(setup_lines)
        parts.append(
            f"""
const {name} = {{
  setup() {{
    {setup_body}
    return () => {render_code};
  }}
}};
""".strip()
        )

        return "\n\n".join(parts)

    def emit_injects(self, injects: list[SymbolId]) -> str:
        method = self.import_table.use_from_preset(import_presets.Instaui.inject())
        names = [self.ctx.names.resolve(inject) for inject in injects]
        return rf"const {{{', '.join(names)}}} = {method}();"

    def emit_provides(self, provides: list[SymbolId]) -> str:
        method = self.import_table.use_from_preset(import_presets.Instaui.provide())
        names = [self.ctx.names.resolve(provide) for provide in provides]
        return rf"{method}({{{', '.join(names)}}});"

    def emit_js_watch_call(self, watchs: list[JsWatchCall]) -> str:
        method = self.import_table.use_from_preset(import_presets.Instaui.js_watch())
        args_list = expression.ListExpr([watch.args for watch in watchs])
        return rf"{method}({self.expr.emit(args_list)});"

    def emit_expr_watch_call(self, watchs: list[ExprWatchCall]) -> str:
        method = self.import_table.use_from_preset(import_presets.Instaui.expr_watch())
        args_list = expression.ListExpr([watch.args for watch in watchs])
        return rf"{method}({self.expr.emit(args_list)});"
