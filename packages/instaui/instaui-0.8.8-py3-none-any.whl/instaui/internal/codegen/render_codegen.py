from instaui.internal import import_presets
from instaui.internal.ast.core import (
    ContentRender,
    Element,
    MatchRender,
    Render,
    VFor,
    ComponentRefRender,
    VIf,
)
from instaui.internal.codegen.component_ref_renderer import ComponentRefRenderer
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.element_renderer import ElementRenderer
from instaui.internal.codegen.expr_codegen import ExpressionCodegen
from instaui.internal.codegen.match_renderer import MatchRenderer
from instaui.internal.codegen.vfor_renderer import VForRenderer
from instaui.internal.codegen.vif_renderer import VIfRenderer


class RenderCodegen:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.expr = ExpressionCodegen(ctx)
        self._element_renderer = ElementRenderer(ctx, render_emitter=self)
        self._vfor_renderer = VForRenderer(ctx, render_emitter=self)
        self._vif_renderer = VIfRenderer(ctx, render_emitter=self)
        self._match_renderer = MatchRenderer(ctx, render_emitter=self)
        self._component_ref_renderer = ComponentRefRenderer(ctx)

    def emit_renders(self, renders: list[Render]) -> str:
        if not renders:
            return "null"

        return f"[{', '.join(self.emit_render(render) for render in renders)}]"

    def emit_render(self, render: Render) -> str:
        method = getattr(self, f"emit_{type(render).__name__}", None)
        if not method:
            raise NotImplementedError(type(render))
        return method(render)

    def emit_Element(self, render: Element) -> str:
        return self._element_renderer.emit(render)

    def emit_VFor(self, render: VFor) -> str:
        return self._vfor_renderer.emit(render)

    def emit_VIf(self, render: VIf) -> str:
        return self._vif_renderer.emit(render)

    def emit_MatchRender(self, render: MatchRender) -> str:
        return self._match_renderer.emit(render)

    def emit_ComponentRefRender(self, render: ComponentRefRender) -> str:
        return self._component_ref_renderer.emit(render.ref)

    def emit_ContentRender(self, content: ContentRender) -> str:
        method = self.ctx.imports.use_from_preset(
            import_presets.Instaui.render_content()
        )
        return f"{method}({self.expr.emit(content.content)})"
