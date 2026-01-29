from typing import Any, Literal, Sequence
from instaui.internal.backend.invocation import BackendInvocation, BackendInvocationKind
from instaui.internal.ui._expr.codec_expr import DataCodecExpr
from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from instaui.internal.ui._expr.maybe_ref_expr import UIMaybeRefExpr
from instaui.internal.ui.file_io._download import DownloadFileBindingOutput
from instaui.internal.ui.js_output import JsOutput
from instaui.internal.ui.path_var import PathTrackerBindable, PathTrackerPipelines
from instaui.internal.ui.reference import VariableReferenceName
from instaui.internal.ui.to_value import ToValue
from instaui.internal.ui.upload import UploadEndpoint
from instaui.internal.ui.variable import Variable
from instaui.internal.ui.str_format import StrFormat
from instaui.internal.ui.event_context import EventContext
from instaui.internal.ui.props_injectable import PropInjectableRef
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.codec.codec_json import json_codec


TBuildMode = Literal["expr", "literal", "shallow"]


class ExprBuilder:
    def __init__(self, ctx: AstBuilderContext) -> None:
        self.ctx = ctx

    def build(self, value: Any, mode: TBuildMode = "expr") -> expression.Expression:
        method = getattr(self, f"build_{type(value).__name__}", None)
        if method:
            return method(value, mode)

        if isinstance(value, PathTrackerBindable):
            return self.build_PathTrackerBindable(value, mode)
        if isinstance(value, Variable):
            return self.build_Variable(value, mode)

        if isinstance(value, JsOutput):
            return self.build_JsOutput(value, mode)

        if isinstance(value, (str, int, float, bool)) or value is None:
            return expression.Literal(value=value)

        if isinstance(value, (list, tuple)):
            return self._build_sequence(value, mode)

        if isinstance(value, dict):
            return self._build_dict(value, mode)

        if isinstance(value, expression.Expression):
            return value

        raise TypeError(f"Unsupported expression value: {value!r}")

    def _build_sequence(
        self, value: Sequence, mode: TBuildMode
    ) -> expression.Expression:
        if mode == "expr":
            return expression.ListExpr([self.build(v, mode) for v in value])

        if mode == "literal":
            return expression.ListLiteral(value=list(value))

        if mode == "shallow":
            return self._build_shallow_literal(value)

        raise AssertionError(mode)

    def _build_dict(self, value: dict, mode: TBuildMode) -> expression.Expression:
        if mode == "expr":
            return expression.ObjectExpr(
                props=[
                    expression.ObjectProperty(k, self.build(v, mode))
                    for k, v in value.items()
                ]
            )

        if mode == "literal":
            return expression.ObjectLiteral(props=value)

        if mode == "shallow":
            return self._build_shallow_literal(value)

        raise AssertionError(mode)

    def _build_shallow_literal(self, value: Any) -> expression.Expression:
        if isinstance(value, expression.Expression):
            return value

        if isinstance(value, list):
            return expression.ListLiteral(value=list(value))

        if isinstance(value, dict):
            return expression.ObjectLiteral(props=dict(value))

        if isinstance(value, (str, int, float, bool)) or value is None:
            return expression.Literal(value=value)

        raise TypeError(f"Unsupported value in shallow literal: {value!r}")

    def object_shallow(self, kwargs: dict) -> expression.ObjectExpr:
        return expression.ObjectExpr(
            props=[
                expression.ObjectProperty(k, self.build(v, "shallow"))
                for k, v in kwargs.items()
                if v is not None
            ]
        )

    def object_expr(
        self,
        kwargs: dict,
        *,
        mode: TBuildMode = "expr",
    ) -> expression.ObjectExpr:
        return expression.ObjectExpr(
            props=[
                expression.ObjectProperty(k, self.build(v, mode))
                for k, v in kwargs.items()
                if v is not None
            ]
        )

    def list_expr(
        self, *, mode: TBuildMode = "expr", values: Sequence[Any]
    ) -> expression.ListExpr:
        return expression.ListExpr([self.build(v, mode) for v in values])

    def list_shallow(self, values: Sequence[Any]) -> expression.ListExpr:
        return expression.ListExpr([self.build(v, "shallow") for v in values])

    def build_Variable(
        self, value: Variable, mode: TBuildMode = "expr"
    ) -> expression.IdentifierRef:
        real_value = value._source if isinstance(value, PathTrackerBindable) else value
        sid = self.ctx.var_mapper.get_id(real_value)
        assert sid is not None, f"Undefined variable: {real_value!r}"
        return expression.IdentifierRef(id=sid)

    def build_PathTrackerBindable(
        self, value: PathTrackerBindable, mode: TBuildMode = "expr"
    ):
        target = self.build(value._source)
        args = self.build(PathTrackerPipelines.to_expr_literal(value))
        return expression.PathTrackerBindableCall(target, args)

    def build_StrFormat(self, value: StrFormat, mode: TBuildMode):
        code = self.build(value.template)
        args = expression.ObjectExpr.from_kwargs(
            code=code,
            args=self.list_shallow(value.args) if value.args else None,
            kws=self.object_shallow(value.kwargs) if value.kwargs else None,
        )

        return expression.StrFormatCall(args)

    def build_EventContext(self, value: EventContext, mode: TBuildMode):
        code = value.path[1:] if value.path[0] == ":" else f"e=> e.{value.path}"
        return expression.RawFunctionExpr(code)

    def build_JsOutput(self, value: JsOutput, mode: TBuildMode):
        return expression.NULL

    def build_DownloadFileBindingOutput(
        self, value: DownloadFileBindingOutput, mode: TBuildMode
    ):
        return expression.NULL

    def build_UploadEndpoint(self, value: UploadEndpoint, mode: TBuildMode):
        ref_id = self.ctx.binding_registry.register(
            BackendInvocation(
                kind=BackendInvocationKind.FILE_UPLOAD,
                fn=value.handler,
                render_ctx=self.ctx.render_ctx,
            )
        )

        return expression.BackendValueRefExpr(ref_id)

    def build_VariableReferenceName(
        self, value: VariableReferenceName, mode: TBuildMode
    ):
        sid = self.ctx.var_mapper.get_id(value.variable)
        assert sid is not None, f"Undefined variable: {value.variable!r}"
        return expression.StringLiteral(expression.IdentifierRef(id=sid))

    def build_PropInjectableRef(self, value: PropInjectableRef, mode: TBuildMode):
        return self.build(value.value, "expr")

    def build_ToValue(self, value: ToValue, mode: TBuildMode):
        return expression.ToValueCall(self.build(value.value))

    def build_UILiteralExpr(self, value: UILiteralExpr, mode: TBuildMode):
        return expression.JsonLiteralExpr(value.value)

    def build_UIMaybeRefExpr(self, value: UIMaybeRefExpr, mode: TBuildMode):
        return self.build(value.value, mode)

    def build_DataCodecExpr(self, expr: DataCodecExpr, mode: TBuildMode):
        return expression.JsonLiteralExpr(json_codec.python_to_json_value(expr.value))
