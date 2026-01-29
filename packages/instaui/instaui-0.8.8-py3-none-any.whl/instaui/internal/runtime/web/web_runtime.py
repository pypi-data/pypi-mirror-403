from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Optional, Union
from instaui import __version__ as _INSTA_VERSION
from instaui import resources
from instaui.constants.runtime import RuntimeMode
from instaui.constants.ui import USER_ASSETS_ICONS_DIR_NAME
from instaui.internal.assets.context import GLOBAL_ASSETS, get_active_assets
from instaui.internal.assets.snapshot import AssetsSnapshot
from instaui.internal.backend.binding import BackendBindingRegistry
from instaui.internal.backend.fastapi.web_backend import FastapiBackend
from instaui.internal.codegen.program_codegen import ProgramCodegen
from instaui.internal.pipeline.ast_build.builder import AstBuilder
from instaui.internal.pipeline.ast_build.context import AstBuildInput
from instaui.internal.pipeline.web_html.html_renderer import (
    HtmlOptions,
    WebHtmlRenderer,
)
from instaui.internal.runtime.assets_init import inject_framework_assets
from instaui.internal.runtime.execution_scope import PageExecutionScope
from instaui.internal.runtime.layout import LayoutContext
from instaui.internal.runtime.render_ctx import RenderContext
from instaui.internal.runtime.runtime_ctx import RuntimeContext
from instaui.internal.runtime.web.config import WebUserLaunchConfig
from instaui.internal.runtime.web.options import (
    WebUserRunOptions,
    WebUserRunWithOptions,
)
from instaui.internal.runtime.web.runtime_services import WebRuntimeServices
from instaui.internal.ui._app import App
from instaui.internal.ui.app_context import get_default_app
from instaui.internal.ui.app_index import new_app
from instaui.internal.router.registry import route_registry
from instaui.internal.pipeline.asset_resolver.backend_resolver import (
    BackendAssetResolver,
)
from instaui.internal.runtime.app_meta import AppMeta, ServerInfo, ServerRoute, AppIcons
from instaui.internal.pipeline.routing.fastapi import FastAPIRouteSyntaxAdapter

from .assets_pipeline import WEB_ASSETS_PIPELINE


class WebRuntime(WebRuntimeServices):
    def __init__(self, config: WebUserLaunchConfig):
        self.backend = FastapiBackend(
            config=config,
            runtimie_services=self,
            user_assets_dir=self.get_user_assets_folder(config.caller_folder_path),
        )
        self.asset_resolver = BackendAssetResolver(self.backend)
        self.route_syntax_adapter = FastAPIRouteSyntaxAdapter()
        self._launch_config = config
        self.binding_registry = BackendBindingRegistry(self.backend)
        self._mode = RuntimeMode.WEB
        self.debug = config.debug
        self._app_meta = AppMeta(
            self._mode,
            _INSTA_VERSION,
            config.debug,
            server_info=ServerInfo(
                watch_url=self.backend.endpoints.WATCH_URL_WITH_PREFIX,
                watch_async_url=self.backend.endpoints.ASYNC_WATCH_URL_WITH_PREFIX,
                event_url=self.backend.endpoints.EVENT_URL_WITH_PREFIX,
                event_async_url=self.backend.endpoints.ASYNC_EVENT_URL_WITH_PREFIX,
                download_url=self.backend.endpoints.DOWNLOAD_URL_WITH_PREFIX,
                assets_url=self.backend.endpoints.INSTAUI_USER_ASSETS_URL_WITH_PREFIX,
                assets_icons_name=USER_ASSETS_ICONS_DIR_NAME,
            ),
        )

        self.routes = route_registry.routes
        self.runtime_ctx = RuntimeContext(binding_registry=self.binding_registry)

        inject_framework_assets()

    def _render_page_core(self, route: str, caller: Callable) -> str:
        layout_ctx = LayoutContext(get_default_app().layouts)

        with new_app(self._mode, debug=self.debug) as app:
            with layout_ctx:
                caller(self.routes[route].fn)

            updated_app_meta = self._update_app_meta(app, route)
            page_assets = get_active_assets()
            assets_snapshot = WEB_ASSETS_PIPELINE.run(GLOBAL_ASSETS, page_assets)

        render_ctx = RenderContext(app_meta=updated_app_meta, route=route)

        ast = AstBuilder(self.runtime_ctx, render_ctx, self.asset_resolver).build(
            self._create_ast_build_input(app, assets_snapshot)
        )
        code = ProgramCodegen(self.runtime_ctx).emit(ast)
        renderer = WebHtmlRenderer()
        html_str = renderer.render(code, self._build_render_options(assets_snapshot))

        return html_str

    def run(self, optons: WebUserRunOptions):
        self.backend.run(optons)

    def run_with(self, options: WebUserRunWithOptions):
        self.backend.run_with(options)

    def _create_ast_build_input(
        self, app: App, assets_pool: AssetsSnapshot
    ) -> AstBuildInput:
        return AstBuildInput(app=app, scopes=app.created_scopes, assets=assets_pool)

    def _build_render_options(self, merged_assets: AssetsSnapshot) -> HtmlOptions:
        import_maps = (
            merged_assets.import_maps
            # | self._options.get_import_maps_cdn_overrides()
        )

        script_tags_body = [
            (self._normalize_script_tag_attrs(script_tag.attrs), script_tag.inline_code)
            for script_tag in merged_assets.script_tags_in_body
        ]

        script_tags_head = [
            (self._normalize_script_tag_attrs(script_tag.attrs), script_tag.inline_code)
            for script_tag in merged_assets.script_tags_in_head
        ]

        return HtmlOptions(
            is_debug=self.debug,
            prefix=self._launch_config.prefix,
            favicon_url=self._normalize_asset_path(
                merged_assets.favicon or resources.FAVICON_PATH
            ),
            css_links=[
                self._normalize_asset_path(css) for css in merged_assets.css_links
            ],
            import_map={
                name: self._normalize_asset_path(link)
                for name, link in import_maps.items()
            },
            style_tags=[
                (style_tag.group_id, style_tag.content)
                for style_tag in merged_assets.style_tags
            ],
            script_tags_in_body=script_tags_body,
            script_tags_in_head=script_tags_head,
        )

    def _normalize_script_tag_attrs(self, attrs: dict[str, Any] | None):
        if not attrs:
            return None

        src = attrs.get("src", None)
        if not src:
            return attrs

        if isinstance(src, Path):
            return attrs | {"src": self._normalize_asset_path(src)}

        return attrs

    def _normalize_asset_path(self, path: Union[str, Path, None]) -> str:
        if path is None:
            return ""
        if isinstance(path, str):
            return path

        return self.asset_resolver.resolve_asset(path)

    def render_fn(self, route: str) -> str:
        return PageExecutionScope.run(
            lambda: self._render_page_core(route, Caller.call)
        )

    async def render_fn_async(self, route: str) -> str:
        return PageExecutionScope.run(
            lambda: self._render_page_core(route, Caller.call_async)
        )

    def get_user_assets_folder(self, base_folder: Path) -> Optional[Path]:
        assets_folder = base_folder.joinpath("assets")
        if assets_folder.exists():
            return assets_folder

        return None

    def _update_app_meta(self, app: App, route: str):
        icons = AppIcons()
        if app._used_icons:
            icons.names = list(app._used_icons)
        if app._used_icons_set:
            icons.sets = list(app._used_icons_set)

        if not icons:
            icons = None

        return self._app_meta.replace(
            app_icons=icons,
            route=ServerRoute(self.route_syntax_adapter.normalize(route)),
        ).to_dict()


class Caller:
    @staticmethod
    def call(fn: Callable):
        return fn()

    @staticmethod
    async def call_async(fn: Callable):
        return await fn()
