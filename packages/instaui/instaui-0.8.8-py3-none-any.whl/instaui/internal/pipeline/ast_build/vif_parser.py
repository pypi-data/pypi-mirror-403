from instaui.internal.pipeline.ast_build.base import RenderBuilderProtocol
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.ui.vif import VIf
from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import AstBuilderContext


class VIfParser:
    def __init__(
        self, ctx: AstBuilderContext, render_builder: RenderBuilderProtocol
    ) -> None:
        self.ctx = ctx
        self._expr_builder = ExprBuilder(ctx)
        self._render_builder = render_builder

    def parse(self, vif: VIf) -> ast_core.VIf:
        return ast_core.VIf(
            self._expr_builder.build(vif._on),
            children=[self._render_builder.build(r) for r in vif._renderables],
        )
