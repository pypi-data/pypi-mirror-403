from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from instaui.internal.assets.snapshot import AssetsSnapshot
from instaui.internal.pipeline.ast_build.component_scope import ComponentScope
from instaui.internal.pipeline.ast_build.symbol_mapper import IdGenerator, SymbolMapper
from instaui.internal.ui._app import App
from instaui.internal.ui._scope import Scope
from instaui.systems.dataclass_system import dataclass

if TYPE_CHECKING:
    from instaui.internal.backend.binding import BackendBindingRegistryBase
    from instaui.internal.runtime.render_ctx import RenderContext
    from instaui.internal.pipeline.asset_resolver.resolver import AssetResolver


class AstBuilderContext:
    def __init__(
        self,
        binding_registry: BackendBindingRegistryBase,
        render_ctx: RenderContext,
        asset_resolver: AssetResolver,
    ) -> None:
        self._shared_id_generator = IdGenerator()
        self.scope_mapper = SymbolMapper(self._shared_id_generator)
        self.var_mapper = SymbolMapper(self._shared_id_generator)
        self.const_var_mapper = SymbolMapper(self._shared_id_generator)
        self.binding_registry = binding_registry
        self._app_ref = object()
        self.render_ctx = render_ctx
        self.asset_resolver = asset_resolver
        # Component Scope Management
        self.component_scope_manager = ComponentScope()

    def get_app_id(self):
        return self.const_var_mapper.get_or_create_id(self._app_ref)


@dataclass(frozen=True)
class AstBuildInput:
    app: App
    scopes: Sequence[Scope]
    assets: AssetsSnapshot
