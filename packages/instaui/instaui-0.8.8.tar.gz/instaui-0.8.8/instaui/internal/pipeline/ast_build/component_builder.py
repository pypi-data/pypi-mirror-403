from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from instaui.internal.ast.symbol import SymbolId
from instaui.internal.pipeline.ast_build.expr_watch_parser import ExprWatchParser
from instaui.internal.pipeline.ast_build.js_watch_parser import JsWatchParser
from instaui.internal.pipeline.ast_build.render_builder import RenderBuilder
from instaui.internal.pipeline.ast_build.variable_decl_builder import (
    VariableDeclBuilder,
)

from instaui.internal.pipeline.ast_build.web_watch_task import WebWatchTaskParser
from instaui.internal.ui._scope import Scope
from instaui.internal.ast import core as ast_core
from instaui.internal.pipeline.ast_build.context import AstBuilderContext
from instaui.internal.ui.vfor_item import VForIndex, VForItem, VForItemKey

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext
    from instaui.internal.runtime.render_ctx import RenderContext


class ComponentBuilder:
    def __init__(
        self,
        runtime_ctx: RuntimeContext,
        render_ctx: RenderContext,
        builder_ctx: AstBuilderContext,
    ) -> None:
        self.runtime_ctx = runtime_ctx
        self.ctx = builder_ctx
        self._variable_builder = VariableDeclBuilder(self.ctx)
        self._render_builder = RenderBuilder(self.ctx, self)
        self._web_watch_parser = WebWatchTaskParser(runtime_ctx, render_ctx, self.ctx)
        self._js_watch_parser = JsWatchParser(self.ctx)
        self._expr_watch_parser = ExprWatchParser(self.ctx)

    def build_component_ref(self, scope: Scope) -> ast_core.ComponentRef:
        cid = self.ctx.scope_mapper.get_or_create_id(scope)

        options = ast_core.ComponentRefVFor()

        for var in scope._injected:
            if isinstance(var, VForIndex):
                options.index.append(self.ctx.var_mapper.get_or_create_id(var))
                continue

            if isinstance(var, VForItem):
                options.value.append(self.ctx.var_mapper.get_or_create_id(var))
                continue

            if isinstance(var, VForItemKey):
                options.item_key.append(self.ctx.var_mapper.get_or_create_id(var))
                continue

        return ast_core.ComponentRef(id=cid, vfor=options or None)

    def build_component_def(self, scope: Scope) -> ast_core.ComponentDef:
        cid = self.ctx.scope_mapper.get_or_create_id(scope)
        comp = ast_core.ComponentDef(id=cid)

        with self.ctx.component_scope_manager.push(comp):
            comp.variables.extend(
                self._variable_builder.build(variable)
                for variable in scope.variable_order
            )

            comp.renders.extend(
                self._render_builder.build(render) for render in scope._renderables
            )
            comp.web_watch_tasks = self._web_watch_parser.parse(scope)

            comp.injects = self._parse_injects(scope)
            comp.provides = self._parse_provides(scope)
            comp.js_watchs = self._js_watch_parser.parse(scope)
            comp.expr_watchs = self._expr_watch_parser.parse(scope)

        return comp

    def _parse_injects(self, scope: Scope) -> Optional[list[SymbolId]]:
        if not scope._injected:
            return None

        return [self.ctx.var_mapper.get_or_create_id(var) for var in scope._injected]

    def _parse_provides(self, scope: Scope) -> Optional[list[SymbolId]]:
        if not scope._provided:
            return None

        return [self.ctx.var_mapper.get_or_create_id(var) for var in scope._provided]
