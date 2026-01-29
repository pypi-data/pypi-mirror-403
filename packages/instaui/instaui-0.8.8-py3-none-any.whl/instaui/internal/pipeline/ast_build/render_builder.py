from __future__ import annotations
from instaui.internal.pipeline.ast_build.base import ComponentBuilderProtocol
from instaui.internal.pipeline.ast_build.element_parser import ElementParser
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.pipeline.ast_build.match_parser import MatchParser
from instaui.internal.pipeline.ast_build.vfor_parser import VForParser
from instaui.internal.pipeline.ast_build.vif_parser import VIfParser
from instaui.internal.ui._scope import Scope
from instaui.internal.ui.match import Match
from instaui.internal.ui.renderable import Renderable
from instaui.internal.ui.element import Element
from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui.vfor import VFor
from instaui.internal.ui.vif import VIf
from instaui.internal.ui.components.content import Content


class RenderBuilder:
    def __init__(
        self, ctx: AstBuilderContext, component_builder: ComponentBuilderProtocol
    ) -> None:
        self.ctx = ctx
        self._expr_builder = ExprBuilder(ctx)
        self._element_parser = ElementParser(ctx, self)
        self._vfor_parser = VForParser(ctx, self)
        self._vif_parser = VIfParser(ctx, self)
        self._match_parser = MatchParser(ctx, self)
        self._component_builder = component_builder

    def build(self, renderable: Renderable) -> ast_core.Render:
        method = getattr(self, f"_build_{type(renderable).__name__}", None)
        if method:
            return method(renderable)

        if isinstance(renderable, Element):
            return self._build_Element(renderable)

        raise ValueError(f"Unsupported renderable type: {type(renderable)}")

    def _build_Element(self, element: Element) -> ast_core.Element:
        return self._element_parser.parse(element)

    def _build_VFor(self, vfor: VFor) -> ast_core.VFor:
        return self._vfor_parser.parse(vfor)

    def _build_Scope(self, scope: Scope) -> ast_core.ComponentRefRender:
        return ast_core.ComponentRefRender(
            ref=self._component_builder.build_component_ref(scope)
        )

    def _build_VIf(self, vif: VIf):
        return self._vif_parser.parse(vif)

    def _build_Match(self, match: Match) -> ast_core.MatchRender:
        return self._match_parser.parse(match)

    def _build_Content(self, content: Content) -> ast_core.ContentRender:
        return ast_core.ContentRender(
            self._expr_builder.build(content._content, "literal")
        )
