from __future__ import annotations
from typing import TYPE_CHECKING
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.component_builder import ComponentBuilder
from instaui.internal.pipeline.ast_build.custom_component_builder import (
    CustomComponentBuilder,
)
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder
from instaui.internal.pipeline.ast_build.plugins_builder import PluginsBuilder
from instaui.internal.pipeline.ast_build.variable_decl_builder import (
    VariableDeclBuilder,
)

from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import (
    AstBuilderContext,
    AstBuildInput,
)

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext
    from instaui.internal.runtime.render_ctx import RenderContext
    from instaui.internal.pipeline.asset_resolver.resolver import AssetResolver


class AstBuilder:
    def __init__(
        self,
        runtime_ctx: RuntimeContext,
        render_ctx: RenderContext,
        asset_resolver: AssetResolver,
    ) -> None:
        self.runtime_ctx = runtime_ctx
        self.ctx = AstBuilderContext(
            runtime_ctx.binding_registry, render_ctx, asset_resolver
        )
        self._variable_builder = VariableDeclBuilder(self.ctx)
        self._expr_builder = ExprBuilder(self.ctx)
        self._component_builder = ComponentBuilder(runtime_ctx, render_ctx, self.ctx)
        self._plugins_builder = PluginsBuilder(runtime_ctx, render_ctx, self.ctx)
        self._custom_component_builder = CustomComponentBuilder(
            runtime_ctx, render_ctx, self.ctx
        )

    def build(self, ast_input: AstBuildInput) -> ast_core.App:
        app = ast_input.app
        scopes = ast_input.scopes

        assert scopes, "App scope not set"

        root = scopes[0]
        root_ref = self._component_builder.build_component_ref(root)

        components = []

        for scope in app.created_scopes:
            components.append(self._component_builder.build_component_def(scope))

        return ast_core.App(
            root=root_ref,
            components=components,
            bootstrap=ast_core.AppBootstrap(
                self.ctx.get_app_id(),
                root_ref,
                meta=expression.ObjectLiteral(self.ctx.render_ctx.app_meta),
                plugins=self._plugins_builder.build(list(ast_input.assets.plugins))
                if ast_input.assets.plugins
                else None,
                custom_components=self._custom_component_builder.build(
                    ast_input.assets.component_dependencies
                )
                if ast_input.assets.component_dependencies
                else None,
            ),
        )
