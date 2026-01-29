from instaui.internal.pipeline.ast_build.base import RenderBuilderProtocol
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.ui.vfor import VFor
from instaui.internal.ast import core as ast_core
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext


class VForParser:
    def __init__(
        self, ctx: AstBuilderContext, render_builder: RenderBuilderProtocol
    ) -> None:
        self.ctx = ctx
        self._expr_builder = ExprBuilder(ctx)
        self._render_builder = render_builder

    def parse(self, vfor: VFor) -> ast_core.VFor:
        key = expression.Literal(vfor._key)

        if vfor._data:
            value = self._expr_builder.build(vfor._data, mode="literal")
        elif vfor._range:
            value = self._expr_builder.object_expr(vfor._range)
        else:
            value = expression.UNDEFINED

        array = ast_core.VForArray(
            expression.Literal(vfor._array_type.value),
            value,
        )

        used_item = None
        used_index = None
        used_key = None

        if vfor._vfor_item._used:
            used_item = self.ctx.var_mapper.get_or_create_id(vfor._vfor_item)
            self.ctx.component_scope_manager.declare_var(used_item)

        if vfor._vfor_index._used:
            used_index = self.ctx.var_mapper.get_or_create_id(vfor._vfor_index)
            self.ctx.component_scope_manager.declare_var(used_index)

        if vfor._vfor_item_key._used:
            used_key = self.ctx.var_mapper.get_or_create_id(vfor._vfor_item_key)
            self.ctx.component_scope_manager.declare_var(used_key)

        return ast_core.VFor(
            key,
            array,
            used_item=used_item,
            used_index=used_index,
            used_key=used_key,
            transition_group=expression.ObjectLiteral(vfor._transition_group_setting)
            if vfor._transition_group_setting
            else None,
            children=[self._render_builder.build(r) for r in vfor._renderables],
        )
