from __future__ import annotations
from instaui.internal.pipeline.ast_build.base import RenderBuilderProtocol
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.ui.match import Match
from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import AstBuilderContext


class MatchParser:
    def __init__(
        self, ctx: AstBuilderContext, render_builder: RenderBuilderProtocol
    ) -> None:
        self.ctx = ctx
        self._expr_builder = ExprBuilder(ctx)
        self._render_builder = render_builder

    def parse(self, match: Match) -> ast_core.MatchRender:
        cond = self._expr_builder.build(match._cond, "literal")

        cases = [
            ast_core.MatchCase(
                value=self._expr_builder.build(case._value, "literal"),
                children=[self._render_builder.build(r) for r in case._renderables],
            )
            for case in match._cases
        ]

        default_case = (
            [self._render_builder.build(r) for r in match._default_case._renderables]
            if match._default_case
            else None
        )

        return ast_core.MatchRender(
            condition=cond,
            cases=cases,
            default_case=default_case,
        )
