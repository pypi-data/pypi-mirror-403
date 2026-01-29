from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Optional, Union
from instaui import __version__ as _INSTA_VERSION
from instaui import resources
from instaui.constants.runtime import RuntimeMode
from instaui.internal.assets.context import GLOBAL_ASSETS, get_active_assets
from instaui.internal.assets.snapshot import AssetsSnapshot
from instaui.internal.ast.expression import RawFunctionExpr
from instaui.internal.codegen.program_codegen import ProgramCodegen
from instaui.internal.pipeline.ast_build.builder import AstBuilder
from instaui.internal.pipeline.ast_build.context import AstBuildInput
from instaui.internal.pipeline.zero_html.html_renderer import (
    HtmlOptions,
    ZeroHtmlRenderer,
)
from instaui.internal.runtime.app_meta import AppMeta
from instaui.internal.runtime.assets_init import inject_framework_assets
from instaui.internal.runtime.execution_scope import PageExecutionScope
from instaui.internal.runtime.layout import LayoutContext
from instaui.internal.runtime.render_ctx import RenderContext
from instaui.internal.runtime.runtime_ctx import RuntimeContext
from instaui.internal.ui._app import App
from instaui.internal.ui.app_context import get_default_app
from instaui.internal.ui.app_index import new_app
from instaui.internal.pipeline.asset_resolver.zero_resolver import ZeroAssetResolver
from .options import ZeroOptions
from .assets_pipeline import ZERO_ASSETS_PIPELINE


class ZeroRuntime:
    def __init__(self, options: Optional[ZeroOptions] = None):
        self._options = options or ZeroOptions()
        self.asset_resolver = ZeroAssetResolver()
        self.mode = RuntimeMode.ZERO
        self._app_meta = AppMeta(self.mode, _INSTA_VERSION, self._options.debug)

        self.ctx = RuntimeContext()

    def run(self, page_fn: Callable, *, output_path: Optional[Path] = None):
        return PageExecutionScope.run(
            lambda: self._run_impl(page_fn, output_path=output_path)
        )

    def _run_impl(self, page_fn: Callable, *, output_path: Optional[Path] = None):
        layout_ctx = LayoutContext(get_default_app().layouts)

        with new_app(self.mode, debug=self._options.debug) as app:
            with layout_ctx:
                page_fn()

            page_assets = get_active_assets()
            inject_framework_assets()
            assets_snapshot = ZERO_ASSETS_PIPELINE.run(GLOBAL_ASSETS, page_assets)

        ast = AstBuilder(
            self.ctx, RenderContext(self._app_meta.to_dict()), self.asset_resolver
        ).build(self._create_ast_build_input(app, assets_snapshot))
        ast.components[0].on_mounted_calls.append(
            RawFunctionExpr(
                r"document.querySelector('zero-loadding').setAttribute('hidden', '')"
            )
        )

        code = ProgramCodegen(self.ctx).emit(ast)
        renderer = ZeroHtmlRenderer()
        html_str = renderer.render(
            code, self._build_render_options(assets_snapshot, self._options)
        )
        if output_path:
            output_path.write_text(html_str, encoding="utf-8")

        return html_str

    def _build_render_options(
        self, merged_assets: AssetsSnapshot, options: ZeroOptions
    ) -> HtmlOptions:
        import_maps = (
            merged_assets.import_maps | self._options.get_import_maps_cdn_overrides()
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
            icons_svg_path=options.icons_svg_path,
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

    def _create_ast_build_input(
        self, app: App, assets_pool: AssetsSnapshot
    ) -> AstBuildInput:
        return AstBuildInput(app=app, scopes=app.created_scopes, assets=assets_pool)
