from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

from instaui import __version__ as _INSTA_VERSION
from instaui import resources
from instaui.constants.runtime import RuntimeMode
from instaui.internal.assets.context import GLOBAL_ASSETS, get_active_assets
from instaui.internal.assets.snapshot import AssetsSnapshot
from instaui.internal.ast.expression import RawFunctionExpr
from instaui.internal.backend.binding import BackendBindingRegistry
from instaui.internal.backend.webview.webview_backend import WebViewBackend
from instaui.internal.codegen.program_codegen import ProgramCodegen
from instaui.internal.pipeline.asset_resolver.webview_resolver import (
    WebViewAssetResolver,
)
from instaui.internal.pipeline.ast_build.builder import AstBuilder
from instaui.internal.pipeline.ast_build.context import AstBuildInput
from instaui.internal.pipeline.routing.fastapi import FastAPIRouteSyntaxAdapter
from instaui.internal.pipeline.webview_html.html_renderer import (
    HtmlOptions,
    WebViewHtmlRenderer,
)
from instaui.internal.router.registry import route_registry
from instaui.internal.runtime.app_meta import AppIcons, AppMeta, ServerRoute
from instaui.internal.runtime.assets_init import inject_framework_assets
from instaui.internal.runtime.layout import LayoutContext
from instaui.internal.runtime.render_ctx import RenderContext
from instaui.internal.runtime.runtime_ctx import RuntimeContext
from instaui.internal.runtime.webview.config import (
    PageBuildStrategy,
    WebViewUserLaunchConfig,
)
from instaui.internal.runtime.webview.options import WebViewUserRunOptions
from instaui.internal.ui._app import App
from instaui.internal.ui.app_context import get_default_app
from instaui.internal.ui.app_index import new_app

from .assets import FileSystemAssetMaterializer, PageAssetManager
from .assets_pipeline import WEBVIEW_ASSETS_PIPELINE

_INDEX_HTML_NAME = "index.html"


class WebViewRuntime:
    def __init__(self, config: WebViewUserLaunchConfig):
        self._launch_config = config
        self.backend = WebViewBackend(config)
        self.asset_materializer = FileSystemAssetMaterializer()

        self.route_syntax_adapter = FastAPIRouteSyntaxAdapter()
        self.binding_registry = BackendBindingRegistry(self.backend)
        self._mode = RuntimeMode.WEBVIEW
        self.debug = config.debug
        self._app_meta = AppMeta(self._mode, _INSTA_VERSION, config.debug)

        self.routes = route_registry.routes
        self.runtime_ctx = RuntimeContext(binding_registry=self.binding_registry)
        self.asset_manager = PageAssetManager(
            assets_root=self._launch_config.assets_path,
            clean_on_start=self._launch_config.clean_assets_on_start,
        )

        inject_framework_assets()

    def _render_page_core(self, route: str) -> str:
        page_dir = self.asset_manager.prepare_page_dir(route)
        layout_ctx = LayoutContext(get_default_app().layouts)

        with new_app(self._mode, debug=self.debug) as app:
            with layout_ctx:
                self.routes[route].fn()

            updated_app_meta = self._update_app_meta(app, route)
            page_assets = get_active_assets()
            assets_snapshot = WEBVIEW_ASSETS_PIPELINE.run(GLOBAL_ASSETS, page_assets)

        render_ctx = RenderContext(app_meta=updated_app_meta, route=route)

        asset_resolver = WebViewAssetResolver(page_dir, self.asset_materializer)

        ast = AstBuilder(self.runtime_ctx, render_ctx, asset_resolver).build(
            self._create_ast_build_input(app, assets_snapshot)
        )

        if self._launch_config.on_page_mounted:
            ast.components[0].on_mounted_calls.append(
                RawFunctionExpr("pywebview.api.on_app_mounted()")
            )

        code = ProgramCodegen(self.runtime_ctx).emit(ast)
        renderer = WebViewHtmlRenderer()
        html_str = renderer.render(
            code, self._build_render_options(assets_snapshot, asset_resolver)
        )

        index_html_path = page_dir / _INDEX_HTML_NAME
        index_html_path.write_text(html_str, encoding="utf-8")
        url = index_html_path.resolve().as_uri()

        self.asset_manager.mark_page_generated(route)

        return url

    def create_window(self, page_url: str = "/"):
        if not self.asset_manager.is_page_generated(page_url):
            url = self._render_page_core(page_url)
        else:
            page_dir = self._launch_config.assets_path.joinpath(page_url)
            url = (page_dir / _INDEX_HTML_NAME).resolve().as_uri()

        return self.backend.create_window(url)

    def run(self, optons: WebViewUserRunOptions):
        self._prebuild_pages()

        auto_create_window = self._launch_config.auto_create_window
        if auto_create_window:
            self.create_window(
                "/" if auto_create_window is True else auto_create_window
            )

        self.backend.run(optons)

    def _run_with_index(
        self, index_page_url: str, optons: WebViewUserRunOptions | None
    ):
        self.backend._run_with_index(index_page_url, optons)

    def _create_ast_build_input(
        self, app: App, assets_pool: AssetsSnapshot
    ) -> AstBuildInput:
        return AstBuildInput(app=app, scopes=app.created_scopes, assets=assets_pool)

    def _build_render_options(
        self, merged_assets: AssetsSnapshot, asset_resolver: WebViewAssetResolver
    ) -> HtmlOptions:
        import_maps = (
            merged_assets.import_maps
            # | self._options.get_import_maps_cdn_overrides()
        )

        script_tags_body = [
            (
                self._normalize_script_tag_attrs(script_tag.attrs, asset_resolver),
                script_tag.inline_code,
            )
            for script_tag in merged_assets.script_tags_in_body
        ]

        script_tags_head = [
            (
                self._normalize_script_tag_attrs(script_tag.attrs, asset_resolver),
                script_tag.inline_code,
            )
            for script_tag in merged_assets.script_tags_in_head
        ]

        return HtmlOptions(
            favicon_url=self._normalize_asset_path(
                merged_assets.favicon or resources.FAVICON_PATH, asset_resolver
            ),
            css_links=[
                self._normalize_asset_path(css, asset_resolver)
                for css in merged_assets.css_links
            ],
            import_map={
                name: self._normalize_asset_path(link, asset_resolver)
                for name, link in import_maps.items()
            },
            style_tags=[
                (style_tag.group_id, style_tag.content)
                for style_tag in merged_assets.style_tags
            ],
            script_tags_in_head=script_tags_head,
            script_tags_in_body=script_tags_body,
        )

    def _normalize_script_tag_attrs(
        self, attrs: dict[str, Any] | None, asset_resolver: WebViewAssetResolver
    ):
        if not attrs:
            return None

        src = attrs.get("src", None)
        if not src:
            return attrs

        if isinstance(src, Path):
            return attrs | {"src": self._normalize_asset_path(src, asset_resolver)}

        return attrs

    def _normalize_asset_path(
        self, path: Union[str, Path, None], asset_resolver: WebViewAssetResolver
    ) -> str:
        if path is None:
            return ""
        if isinstance(path, str):
            return path

        return asset_resolver.resolve_asset(path)

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

    def _is_param_route(self, route: str) -> bool:
        return "{" in route and "}" in route

    def _resolve_prebuild_routes(self) -> list[str]:
        strategy = self._launch_config.page_build_strategy
        prebuild = self._launch_config.prebuild_routes

        all_routes = list(self.routes.keys())

        if strategy == PageBuildStrategy.EAGER:
            routes_to_build = all_routes if prebuild is None else prebuild
        else:
            routes_to_build = prebuild or []

        # Check for parameterized routes
        param_routes = [r for r in routes_to_build if self._is_param_route(r)]
        unknown_routes = [r for r in routes_to_build if r not in self.routes]

        if param_routes or unknown_routes:
            msg_lines = ["Cannot prebuild the following routes in WebView mode:"]
            for r in param_routes:
                msg_lines.append(f"  - Parameterized route: {r}")
            for r in unknown_routes:
                msg_lines.append(f"  - Unknown route: {r}")
            msg_lines.append(
                "Prebuild routes must be fully static paths defined in @ui.page."
            )
            raise ValueError("\n".join(msg_lines))

        return routes_to_build

    def _prebuild_pages(self) -> None:
        routes_to_build = self._resolve_prebuild_routes()
        if not routes_to_build:
            return

        for route in routes_to_build:
            self._render_page_core(route)
