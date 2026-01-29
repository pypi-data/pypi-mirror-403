from __future__ import annotations
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from instaui.internal.ui.renderable import Renderable
    from instaui.internal.ui._scope import Scope
    from instaui.internal.ast.core import Render, ComponentRef, ComponentDef
    from instaui.internal.ast.expression import Expression, ListExpr, ObjectExpr
    from instaui.internal.pipeline.ast_build.expr_builder import TBuildMode


class RenderBuilderProtocol(Protocol):
    def build(self, renderable: Renderable) -> Render: ...


class ExprBuilderProtocol(Protocol):
    def build(self, value: Expression, mode: TBuildMode = "expr") -> Expression: ...

    def list_shallow(self, values: list) -> ListExpr: ...

    def object_shallow(self, kwargs: dict) -> ObjectExpr: ...


class ComponentBuilderProtocol(Protocol):
    def build_component_ref(self, scope: Scope) -> ComponentRef: ...

    def build_component_def(self, scope: Scope) -> ComponentDef: ...
