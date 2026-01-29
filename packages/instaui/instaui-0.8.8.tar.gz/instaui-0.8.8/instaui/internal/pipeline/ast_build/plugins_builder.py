from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Sequence
from instaui.internal.assets import PluginDependencyInfo
from instaui.internal.assets.plugin import PluginOptionsBuilder
from instaui.internal.ast.property_key import StringKey
from instaui.internal.pipeline.ast_build.component_builder import ComponentBuilder
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.ast import core as ast_core
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui._scope import Scope

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext
    from instaui.internal.runtime.render_ctx import RenderContext


class PluginsBuilder:
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
        self, plugins: Sequence[PluginDependencyInfo]
    ) -> Optional[list[ast_core.Plugin]]:
        if not plugins:
            return None

        return [
            ast_core.Plugin(
                url=expression.StringLiteral(
                    self.ctx.asset_resolver.resolve_asset(plugin.esm)
                ),
                options=self._parse_options(plugin.options),
            )
            for plugin in plugins
        ]

    def _parse_options(self, options: Optional[dict | PluginOptionsBuilder]):
        if options is None:
            return None

        if isinstance(options, dict):
            return expression.JsonLiteralExpr(options)

        opts_build_fn = options

        return self._expr_builder.object_expr(
            opts_build_fn(self._parse_option_key, self._parse_scope)
        )

    def _parse_scope(self, scope: Scope):
        return expression.IdentifierRef(self.ctx.scope_mapper.get_or_create_id(scope))

    def _parse_option_key(self, key: str):
        return StringKey(key)
