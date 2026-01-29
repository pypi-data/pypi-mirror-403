from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from instaui.internal.ast import expression
from instaui.internal.backend.invocation import BackendInvocation, BackendInvocationKind
from instaui.internal.pipeline.ast_build.exception import AstBuildError
from instaui.internal.pipeline.ast_build.pre_setup_parser import PreSetupParser
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.pipeline.ast_build.utils import ui_bindings_utils

from instaui.internal.ui._scope import Scope
from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui.enums import OutputSetType
from instaui.internal.ui.web_computed import WebComputed
from instaui.internal.ui.web_watch import WebWatch

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext
    from instaui.internal.runtime.render_ctx import RenderContext


class WebWatchTaskParser:
    def __init__(
        self,
        runtime_ctx: RuntimeContext,
        render_ctx: RenderContext,
        builder_ctx: AstBuilderContext,
    ) -> None:
        self.runtime_ctx = runtime_ctx
        self.render_ctx = render_ctx
        self._expr_builder = ExprBuilder(builder_ctx)
        self.pre_setup_parser = PreSetupParser(self._expr_builder)

    def parse(self, scope: Scope) -> Optional[list[ast_core.WebWatchTask]]:
        result: list[ast_core.WebWatchTask] = []
        if scope._web_computeds:
            result.extend(
                self._from_computed(computed) for computed in scope._web_computeds
            )

        if scope._web_watchs:
            result.extend(self._from_watch(watch) for watch in scope._web_watchs)

        return result or None

    def _from_computed(self, computed: WebComputed) -> ast_core.WebWatchTask:
        try:
            f_type = ui_bindings_utils.py_function_type(computed._fn)
            f_type = ui_bindings_utils.normalize_f_type(f_type)

            outputs = [computed, *computed._extend_outputs]

            inputs, slients, datas = ui_bindings_utils.analyze_observable_inputs(
                computed._inputs or []
            )

            slients = ui_bindings_utils.normalize_int_values(slients)
            datas = ui_bindings_utils.normalize_int_values(datas)

            output_types = ui_bindings_utils.normalize_int_values(
                [
                    OutputSetType.Ref.value,
                    *[x._to_event_output_type().value for x in outputs[1:]],
                ]
            )

            pre_setup = self.pre_setup_parser.parse(computed._pre_setup)

            ref_id = self.runtime_ctx.binding_registry.register(
                BackendInvocation(
                    kind=BackendInvocationKind.COMPUTED,
                    fn=computed._fn,
                    spec=computed._export_invocation_spec(),
                    render_ctx=self.render_ctx,
                )
            )

            fn = ast_core.BackendFunctionRef(ref_id)
            args = expression.ObjectExpr.from_kwargs(
                type=expression.Literal("c"),
                inputs=self._expr_builder.list_expr(mode="literal", values=inputs)
                if inputs
                else None,
                outputs=self._expr_builder.list_expr(mode="literal", values=outputs)
                if outputs
                else None,
                opTypes=expression.ListLiteral(list(output_types))
                if output_types
                else None,
                slient=expression.ListLiteral(list(slients)) if slients else None,
                data=expression.ListLiteral(list(datas)) if datas else None,
                fType=expression.Literal(f_type) if f_type else None,
                preSetup=pre_setup,
            )

            return ast_core.WebWatchTask(computed._source_span_, fn, args)
        except Exception as e:
            raise AstBuildError(
                f"Failed to build {computed}: {e}", computed._source_span_
            )

    def _from_watch(self, watch: WebWatch) -> ast_core.WebWatchTask:
        try:
            f_type = ui_bindings_utils.py_function_type(watch._fn)
            f_type = ui_bindings_utils.normalize_f_type(f_type)
            outputs = list(watch._outputs or [])

            inputs, slients, datas = ui_bindings_utils.analyze_observable_inputs(
                watch._inputs
            )
            slients = ui_bindings_utils.normalize_int_values(slients)
            datas = ui_bindings_utils.normalize_int_values(datas)

            output_types = ui_bindings_utils.normalize_int_values(
                [x._to_event_output_type().value for x in outputs]
            )

            pre_setup = self.pre_setup_parser.parse(watch._pre_setup)

            ref_id = self.runtime_ctx.binding_registry.register(
                BackendInvocation(
                    kind=BackendInvocationKind.WATCH,
                    fn=watch._fn,
                    spec=watch._export_invocation_spec(),
                    render_ctx=self.render_ctx,
                )
            )

            fn = ast_core.BackendFunctionRef(ref_id)
            args = expression.ObjectExpr.from_kwargs(
                type=expression.Literal("w"),
                inputs=self._expr_builder.list_expr(mode="literal", values=inputs)
                if inputs
                else None,
                outputs=self._expr_builder.list_expr(mode="literal", values=outputs)
                if outputs
                else None,
                opTypes=expression.ListLiteral(list(output_types))
                if output_types
                else None,
                slient=expression.ListLiteral(list(slients)) if slients else None,
                data=expression.ListLiteral(list(datas)) if datas else None,
                fType=expression.Literal(f_type) if f_type else None,
                preSetup=pre_setup,
                immediate=None
                if watch._immediate
                else expression.Literal(watch._immediate),
                deep=None if watch._deep else expression.Literal(watch._deep),
                once=expression.Literal(watch._once) if watch._once else None,
                flush=expression.Literal(watch._flush) if watch._flush else None,
            )

            return ast_core.WebWatchTask(watch._source_span_, fn, args)
        except Exception as e:
            raise AstBuildError(f"Failed to build {watch}: {e}", watch._source_span_)
