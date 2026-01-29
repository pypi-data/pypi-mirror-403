from typing import Any
from instaui.systems import json_system
from instaui.internal import import_presets
from instaui.internal.ast.expression import (
    Expression,
    JsonLiteralExpr,
    Literal,
    IdentifierRef,
    MemberExpr,
    CallExpr,
    ObjectLiteral,
    ArrowFunctionExpr,
    ListLiteral,
    ObjectProperty,
    RawFunctionExpr,
    ObjectExpr,
    ListExpr,
    PathTrackerBindableCall,
    StrFormatCall,
    NullExpr,
    StringLiteral,
    UndefinedExpr,
    BackendValueRefExpr,
    ToValueCall,
)
from instaui.internal.ast.property_key import ExpressionKey, StringKey
from instaui.internal.codegen.context.file_ctx import FileCodegenContext


class ExpressionCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx

    def emit(self, expr: Expression) -> str:
        method = getattr(self, f"_emit_{type(expr).__name__}", None)
        if method:
            return method(expr)

        return self._emit_primitive(expr)

    def _emit_primitive(self, expr: Any) -> str:
        if isinstance(expr, bool):
            return "true" if expr else "false"

        if isinstance(expr, (str, int, float)):
            return repr(expr)

        if isinstance(expr, list):
            return "[" + ", ".join(self._emit_primitive(v) for v in expr) + "]"

        if isinstance(expr, dict):
            return (
                "{"
                + ", ".join(
                    f"{k}: {self._emit_primitive(v)}"
                    for k, v in expr.items()
                    if v is not None
                )
                + "}"
            )

        raise NotImplementedError(type(expr))

    def _emit_Literal(self, expr: Literal) -> str:
        return self.emit(expr.value)

    def _emit_IdentifierRef(self, expr: IdentifierRef) -> str:
        sid = expr.id
        return self.ctx.names.resolve(sid)

    def _emit_MemberExpr(self, expr: MemberExpr) -> str:
        obj = expr.obj
        member = expr.member
        return f"{self.emit(obj)}.{member}"

    def _emit_CallExpr(self, expr: CallExpr) -> str:
        callee = expr.callee
        args = expr.args
        args_code = ""
        if args:
            args_code = ", ".join(self.emit(a) for a in args)

        target = self.emit(callee)
        return f"{target}({args_code})"

    def _emit_ObjectLiteral(self, expr: ObjectLiteral) -> str:
        return self._emit_primitive(expr.props)

    def _emit_ArrowFunctionExpr(self, expr: ArrowFunctionExpr) -> str:
        body = expr.body
        return f"({self.emit(expr.params) if expr.params else ''}) => {self.emit(body) if body else r'{}'}"

    def _emit_ListLiteral(self, expr: ListLiteral) -> str:
        return self._emit_primitive(expr.value)

    def _emit_RawFunctionExpr(self, expr: RawFunctionExpr) -> str:
        return expr.js_code

    def _emit_ObjectExpr(self, expr: ObjectExpr) -> str:
        parts = []
        for prop in expr.props:
            parts.append(self._emit_property(prop))

        return "{" + ", ".join(parts) + "}"

    def _emit_ListExpr(self, expr: ListExpr) -> str:
        items = [self.emit(v) for v in expr.value]
        return "[" + ", ".join(items) + "]"

    def _emit_PathTrackerBindableCall(self, expr: PathTrackerBindableCall):
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.track_path())
        return f"{method}({self.emit(expr.target)},{self.emit(expr.args)})"

    def _emit_StrFormatCall(self, expr: StrFormatCall):
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.str_format())
        return f"{method}({self.emit(expr.args)})"

    def _emit_NullExpr(self, expr: NullExpr) -> str:
        return "null"

    def _emit_UndefinedExpr(self, expr: UndefinedExpr) -> str:
        return "undefined"

    def _emit_JsonLiteralExpr(self, expr: JsonLiteralExpr) -> str:
        return json_system.to_json_str(expr.value)

    def _emit_BackendValueRefExpr(self, expr: BackendValueRefExpr) -> str:
        return self._emit_primitive(
            self.ctx.root.binding_registry.get_value(expr.ref_id)
        )

    def _emit_StringLiteral(self, expr: StringLiteral) -> str:
        return json_system.to_json_str(
            self.emit(expr.value) if isinstance(expr.value, Expression) else expr.value
        )

    def _emit_ToValueCall(self, expr: ToValueCall) -> str:
        method = self.ctx.imports.use_from_preset(import_presets.Instaui.to_value())
        return f"{method}({self.emit(expr.value)})"

    def _emit_property(self, prop: ObjectProperty) -> str:
        if isinstance(prop.key, str):
            key_str = prop.key

        if isinstance(prop.key, StringKey):
            key_str = f'"{prop.key.value}"'
        elif isinstance(prop.key, ExpressionKey):
            key_str = self.emit(prop.key.expr)

        if prop.shorthand:
            return key_str

        if prop.value is None:
            value_str = "undefined"
        else:
            value_str = self.emit(prop.value)

        return f"{key_str}: {value_str}"
