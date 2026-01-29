from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Sequence
from instaui.internal.assets.snapshot import ComponentDependencySnapshot
from instaui.internal.pipeline.ast_build.component_builder import ComponentBuilder
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.ast import core as ast_core
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext
    from instaui.internal.runtime.render_ctx import RenderContext


class CustomComponentBuilder(ComponentBuilder):
    def __init__(
        self,
        runtime_ctx: RuntimeContext,
        render_ctx: RenderContext,
        builder_ctx: AstBuilderContext,
    ) -> None:
        self.runtime_ctx = runtime_ctx
        self.ctx = builder_ctx
        self._expr_builder = ExprBuilder(self.ctx)
        self._component_builder = ComponentBuilder(runtime_ctx, render_ctx, self.ctx)

    def build(
        self, components: Sequence[ComponentDependencySnapshot]
    ) -> Optional[list[ast_core.CustomComponent]]:
        if not components:
            return None

        return [
            ast_core.CustomComponent(
                name=expression.StringLiteral(comp.tag),
                url=expression.StringLiteral(
                    self.ctx.asset_resolver.resolve_asset(comp.esm)
                ),
            )
            for comp in components
        ]
