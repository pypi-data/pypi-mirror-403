from __future__ import annotations
from typing import TYPE_CHECKING

from instaui.internal.ast import core as ast_core
from instaui.internal.ast import expression
from instaui.internal.backend.invocation import BackendInvocation, BackendInvocationKind
from instaui.internal.pipeline.ast_build.exception import AstBuildError
from instaui.internal.pipeline.ast_build.pre_setup_parser import PreSetupParser
from instaui.internal.pipeline.ast_build.utils import ui_bindings_utils
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.ui.const_data import ConstData
from instaui.internal.ui.element_ref import ElementRef
from instaui.internal.ui.expr_event import ExprEvent
from instaui.internal.ui.js_fn import JsFn
from instaui.internal.ui.ref_base import RefBase
from instaui.internal.ui.custom_var import CustomVar
from instaui.internal.ui.expr_computed import ExprComputed
from instaui.internal.ui.web_computed import WebComputed
from instaui.internal.ui.web_event import WebEvent
from instaui.internal.ui.js_computed import JsComputed
from instaui.internal.ui.js_event import JsEvent


if TYPE_CHECKING:
    from instaui.internal.ui.variable import Variable


class VariableDeclBuilder:
    def __init__(self, ctx: AstBuilderContext) -> None:
        self.ctx = ctx
        self.expr_builder = ExprBuilder(ctx)
        self.pre_setup_parser = PreSetupParser(self.expr_builder)

    def build(self, variable: Variable) -> ast_core.VariableDecl:
        try:
            method = getattr(self, f"_build_{type(variable).__name__}", None)
            if method:
                return method(variable)

            if isinstance(variable, CustomVar):
                return self._build_CustomRef(variable)

            raise ValueError(f"Unsupported variable type: {type(variable)}")
        except Exception as e:
            raise AstBuildError(
                f"Failed to build {variable}: {e}",
                variable._source_span_,  # type: ignore
            )

    def _build_ConstData(self, variable: ConstData) -> ast_core.ConstDataDecl:
        sid = self._declare_var(variable)
        return ast_core.ConstDataDecl(
            variable._source_span_, sid, self.expr_builder.build(variable.value)
        )

    def _build_RefBase(self, variable: RefBase) -> ast_core.RefDecl:
        sid = self._declare_var(variable)
        args = self.expr_builder.object_shallow(
            {
                "value": variable._value,
                "deepCompare": variable._deep_compare or None,
            }
        )

        return ast_core.RefDecl(variable._source_span_, sid, args)

    def _build_WebComputed(self, variable: WebComputed) -> ast_core.BackendComputedDecl:
        sid = self._declare_var(variable)

        args = self.expr_builder.object_shallow(
            {
                "init": variable._init_value,
                "deepCompare": variable._deep_compare_on_input or None,
            }
        )

        return ast_core.BackendComputedDecl(variable._source_span_, sid, args)

    def _build_JsComputed(self, variable: JsComputed) -> ast_core.JsComputedDecl:
        sid = self._declare_var(variable)

        inputs, _, _ = ui_bindings_utils.analyze_observable_inputs(
            variable._inputs or []
        )

        args = self.expr_builder.object_shallow(
            {
                "code": variable.code,
                "inputs": self.expr_builder.list_shallow(inputs) or None,
                "asyncInit": variable._async_init_value,
                "deepEqOnInput": 1
                if variable._deep_compare_on_input is not False
                else None,
                "tool": variable._tool,
            }
        )

        return ast_core.JsComputedDecl(variable._source_span_, sid, args)

    def _build_JsEvent(self, variable: JsEvent) -> ast_core.JsEventDecl:
        sid = self._declare_var(variable)
        args = self.expr_builder.object_shallow(
            {
                "code": variable._code,
                "inputs": self.expr_builder.list_shallow(variable._inputs) or None,
                "outputs": self.expr_builder.list_shallow(variable._outputs) or None,
                "iptTypes": ui_bindings_utils.inputs_to_types(variable._inputs),
                "opTypes": ui_bindings_utils.outputs_to_types(variable._outputs),
            }
        )

        return ast_core.JsEventDecl(
            variable._source_span_,
            sid,
            args,
        )

    def _build_WebEvent(self, variable: WebEvent) -> ast_core.BackendEventDecl:
        sid = self._declare_var(variable)
        ref_id = self.ctx.binding_registry.register(
            BackendInvocation(
                kind=BackendInvocationKind.EVENT,
                fn=variable._fn,
                spec=variable._export_invocation_spec(),
                render_ctx=self.ctx.render_ctx,
            )
        )

        hkey = self.ctx.binding_registry.get_value(ref_id)

        f_type = ui_bindings_utils.py_function_type(variable._fn)
        pre_setup = self.pre_setup_parser.parse(variable._pre_setup)
        args = self.expr_builder.object_shallow(
            {
                "hKey": hkey,
                "fType": None if f_type == "sync" else f_type,
                "inputs": self.expr_builder.list_shallow(variable._inputs) or None,
                "outputs": self.expr_builder.list_shallow(variable._outputs) or None,
                "iptTypes": ui_bindings_utils.inputs_to_types(variable._inputs)
                if variable._inputs
                else None,
                "opTypes": ui_bindings_utils.outputs_to_types(variable._outputs),
                "preSetup": pre_setup,
            }
        )

        return ast_core.BackendEventDecl(variable._source_span_, sid, args)

    def _build_ElementRef(self, variable: ElementRef) -> ast_core.ElementRefDecl:
        sid = self._declare_var(variable)
        return ast_core.ElementRefDecl(variable._source_span_, sid)

    def _build_ExprComputed(self, variable: ExprComputed) -> ast_core.ExprComputedDecl:
        sid = self._declare_var(variable)

        args = self.expr_builder.object_shallow(
            {
                "code": expression.Literal(variable.code),
                "bind": self.expr_builder.object_shallow(variable._bindings)
                if variable._bindings
                else None,
            }
        )

        return ast_core.ExprComputedDecl(variable._source_span_, sid, args)  # type: ignore

    def _build_ExprEvent(self, variable: ExprEvent) -> ast_core.ExprEventDecl:
        sid = self._declare_var(variable)
        args = self.expr_builder.object_shallow(
            {
                "code": expression.Literal(variable._code),
                "bind": self.expr_builder.object_shallow(variable._bindings) or None,
            }
        )

        return ast_core.ExprEventDecl(variable._source_span_, sid, args)

    def _build_JsFn(self, variable: JsFn) -> ast_core.JsFnDecl:
        sid = self._declare_var(variable)
        code = variable.code
        if variable._execute_immediately:
            code = f"({code})()"
        return ast_core.JsFnDecl(
            variable._source_span_, sid, expression.RawFunctionExpr(code)
        )

    def _build_CustomRef(self, variable: CustomVar) -> ast_core.CustomRefDecl:
        sid = self._declare_var(variable)
        params = []
        if variable._args is not None:
            if isinstance(variable._args, tuple):
                params = [self.expr_builder.build(arg) for arg in variable._args]
            else:
                params = [self.expr_builder.build(variable._args)]

        return ast_core.CustomRefDecl(
            variable._source_span_,
            sid,
            variable._method.module_name,
            variable._method.method_name,
            params,
        )

    def _declare_var(self, variable: Variable):
        sid = self.ctx.var_mapper.get_or_create_id(variable)
        self.ctx.component_scope_manager.declare_var(sid)
        return sid
