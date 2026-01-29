from instaui.internal import import_presets
from instaui.internal.ast.core import (
    BackendComputedDecl,
    CustomRefDecl,
    ElementRefDecl,
    ExprComputedDecl,
    ExprEventDecl,
    JsComputedDecl,
    JsEventDecl,
    JsFnDecl,
    RefDecl,
    VariableDecl,
    BackendEventDecl,
    ConstDataDecl,
)
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.exception import CodegenError
from .expr_codegen import ExpressionCodegen


class VariableDeclCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.import_table = ctx.imports
        self.expr = ExpressionCodegen(ctx)

    def emit(self, var: VariableDecl) -> str:
        try:
            method = getattr(self, f"_emit_variable_{type(var).__name__}", None)
            if not method:
                raise NotImplementedError(type(var))
            return method(var)
        except Exception as e:
            raise CodegenError(f"Failed to generate code for {var}: {e}", var.source)

    def _emit_variable_RefDecl(self, var: RefDecl):
        method = self.import_table.use_from_preset(import_presets.Instaui.ref())
        target = self.ctx.names.resolve(var.target)
        args = self.expr.emit(var.args)
        return f"const {target} = {method}({args});"

    def _emit_variable_JsComputedDecl(self, var: JsComputedDecl):
        method = self.import_table.use_from_preset(import_presets.Instaui.js_computed())
        target = self.ctx.names.resolve(var.target)
        args = self.expr.emit(var.args)
        return f"const {target} = {method}({args});"

    def _emit_variable_BackendComputedDecl(self, var: BackendComputedDecl):
        method = self.import_table.use_from_preset(
            import_presets.Instaui.web_computed_ref()
        )
        target = self.ctx.names.resolve(var.target)

        computed_code = rf"const {target} = {method}({self.expr.emit(var.args)});"
        return computed_code

    def _emit_variable_JsEventDecl(self, var: JsEventDecl):
        method = self.import_table.use_from_preset(import_presets.Instaui.js_event())
        target = self.ctx.names.resolve(var.target)
        args = self.expr.emit(var.args)
        return f"const {target} = {method}({args});"

    def _emit_variable_BackendEventDecl(self, var: BackendEventDecl):
        method = self.import_table.use_from_preset(import_presets.Instaui.web_event())
        target = self.ctx.names.resolve(var.target)

        return rf"const {target} = {method}({self.expr.emit(var.args)});"

    def _emit_variable_ConstDataDecl(self, var: ConstDataDecl):
        target = self.ctx.names.resolve(var.target)
        value = self.expr.emit(var.value)
        return f"const {target} = {value};"

    def _emit_variable_ElementRefDecl(self, var: ElementRefDecl):
        method = self.ctx.imports.use_from_preset(import_presets.Vue.ref())
        target = self.ctx.names.resolve(var.target)
        return f"const {target} = {method}();"

    def _emit_variable_ExprComputedDecl(self, var: ExprComputedDecl):
        method = self.ctx.imports.use_from_preset(
            import_presets.Instaui.expr_computed()
        )
        target = self.ctx.names.resolve(var.target)
        return f"const {target} = {method}({self.expr.emit(var.args)});"

    def _emit_variable_ExprEventDecl(self, var: ExprEventDecl):
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.expr_event())
        target = self.ctx.names.resolve(var.target)
        return f"const {target} = {method}({self.expr.emit(var.args)});"

    def _emit_variable_JsFnDecl(self, var: JsFnDecl):
        target = self.ctx.names.resolve(var.target)
        return f"const {target} = {self.expr.emit(var.fn)};"

    def _emit_variable_CustomRefDecl(self, var: CustomRefDecl):
        method = self.ctx.imports.use(module=var.module, name=var.name)
        target = self.ctx.names.resolve(var.target)
        args = ", ".join(self.expr.emit(p) for p in var.params) if var.params else ""
        return f"const {target} = {method}({args});"
