from __future__ import annotations
from contextlib import contextmanager
import contextvars
from pathlib import Path
from typing import TYPE_CHECKING, Any, Hashable, Optional, Union
from instaui.internal.assets.component_dep import ComponentDependencyInfo
from instaui.internal.assets.css_assets import CssAsset, CssRole
from instaui.internal.assets.plugin import PluginDependencyInfo, PluginOptionsBuilder
from instaui.internal.assets.script_assets import (
    JSAsset,
    ScriptLoading,
    ScriptPosition,
)
from instaui.internal.assets.style_assets import StyleTag
from instaui.internal.context import in_page_context
from .base import AssetsDeclaration

if TYPE_CHECKING:
    from instaui.internal.ui.element import Element

GLOBAL_ASSETS = AssetsDeclaration()
LOCAL_ASSETS: contextvars.ContextVar[Optional[AssetsDeclaration]] = (
    contextvars.ContextVar("local_assets", default=None)
)


@contextmanager
def enter_assets_context():
    token = LOCAL_ASSETS.set(AssetsDeclaration())
    try:
        yield
    finally:
        LOCAL_ASSETS.reset(token)


def get_active_assets() -> AssetsDeclaration:
    """
    Return the AssetsPool that should actually be written based on context.
    """
    if in_page_context():
        local = LOCAL_ASSETS.get()
        if local is None:
            local = AssetsDeclaration()
            LOCAL_ASSETS.set(local)
        return local
    else:
        return GLOBAL_ASSETS


def add_css_link(
    css: Union[Path, str],
    *,
    role: Union[str, CssRole] = CssRole.COMPONENT,
    namespace: Optional[Hashable] = None,
):
    """Add a CSS link to the HTML document."""
    role = CssRole(role) if isinstance(role, str) else role
    get_active_assets().css_links.add(css, namespace=namespace, role=role)


def remove_css_link(
    css: Union[Path, str, CssAsset],
    *,
    role: Union[str, CssRole] = CssRole.COMPONENT,
    namespace: Optional[Hashable] = None,
):
    role = CssRole(role) if isinstance(role, str) else role
    get_active_assets().css_links.remove(css, namespace=namespace, role=role)


def use_favicon(path: Path):
    """Set the favicon of the HTML document.

    Args:
        favicon (Path): The path to the favicon.
    """
    get_active_assets().favicon = path


def add_import_map(name: str, link: Union[str, Path]):
    """Add an import map to the HTML document."""
    get_active_assets().import_maps[name] = link


def register_plugin(
    name: str,
    esm: Path,
    *,
    externals: Optional[dict[str, Path]] = None,
    css: Optional[list[Union[str, Path, CssAsset]]] = None,
    options: Optional[dict | PluginOptionsBuilder] = None,
):
    """
    Register a plugin

    Args:
        name (str): Plugin name
        esm (Path): Path to plugin's ESM file. Format should match vue.js plugins
        externals (Optional[dict[str, Path]], optional): External dependencies for plugin JS implementation. Defaults to None.
        css (Optional[list[Path]], optional): List of CSS file paths for the plugin. Defaults to None.
        options (Optional[dict | PluginOptionsBuilder], optional): Plugin options. Defaults to None.

    Example:
    .. code-block:: python
        from instaui import custom

        # Basic usage
        custom.register_plugin("my-plugin", Path(__file__).parent / "my-plugin.esm.js")

        # With external dependencies
        custom.register_plugin(
            "my-plugin",
            Path(__file__).parent / "my-plugin.esm.js",
            externals={"echarts": Path(__file__).parent / "echarts.esm.js"})

        # With install method options
        custom.register_plugin(..., options = {'opt1': 'value1', 'opt2': 'value2'})

        # With component-dependent options (only needed for complex plugins that define components, like vue-router)
        from instaui import custom

        def parse_scope(self, parse_key: StringKeyFn, parse_scope: ParseScopeFn):
            # parse_key ensures JS object keys are properly quoted
            # parse_scope translates Scope objects into component references
            return {parse_key(k): parse_scope(v) for k, v in self.routes.items()}

        custom.register_plugin(..., options = parse_scope)
    """
    info = PluginDependencyInfo(
        f"plugin/{name}", esm, externals or {}, css or [], options=options
    )
    get_active_assets().plugins.add(info)
    return info


def clear_registered_plugins():
    get_active_assets().plugins.clear()


def add_js_inline(
    code: str,
    *,
    module: bool = False,
    position: ScriptPosition = "body",
    attrs: Optional[dict[str, Any]] = None,
) -> None:
    """
    Add inline JavaScript code to the document.

    Args:
        code: JavaScript source code.
        module: Whether to emit <script type="module">.
        position: Where to inject the script: "head" or "body".
        attrs: Extra attributes for the <script> tag (e.g. nonce, crossorigin, data-*).

    Example:
        ui.add_js_inline("console.log('hi')", module=True)
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("code must be a non-empty string")

    asset = JSAsset(
        kind="inline",
        source=code,
        module=module,
        position=position,
        attrs=attrs or {},
    )

    get_active_assets().js_asset.append(asset)


def add_js_file(
    path: Path | str,
    *,
    module: bool = False,
    loading: ScriptLoading = "blocking",
    position: ScriptPosition = "body",
    attrs: Optional[dict[str, Any]] = None,
) -> None:
    """
    Add a local JavaScript file as an asset.

    The file will be handled by the runtime (e.g. registered as a static file in web mode).

    Args:
        path: Path to the JS file.
        module: Whether to emit <script type="module">.
        loading: Script loading behavior.
        position: Where to inject the script tag.
        attrs: Extra script tag attributes.

    Example:
        ui.add_js_file(Path("assets/app.js"), module=True)
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(p)

    if not p.is_file():
        raise ValueError(f"Not a file: {p}")

    asset = JSAsset(
        kind="file",
        source=p,
        module=module,
        loading=loading,
        position=position,
        attrs=attrs or {},
    )

    get_active_assets().js_asset.append(asset)


def remove_js_file(path: Path | str):
    p = Path(path)

    if not p.exists():
        return

    if not p.is_file():
        raise ValueError(f"Not a file: {p}")

    target = p.resolve()
    assets = get_active_assets().js_asset

    for i in range(len(assets) - 1, -1, -1):
        asset = assets[i]

        if asset.kind != "file":
            continue

        try:
            src = Path(asset.source).resolve()
        except Exception:
            continue

        if src == target:
            del assets[i]


def add_js_url(
    url: str,
    *,
    module: bool = False,
    loading: ScriptLoading = "blocking",
    position: ScriptPosition = "body",
    attrs: Optional[dict[str, Any]] = None,
) -> None:
    """
    Add a remote JavaScript file via URL.

    Args:
        url: Absolute or protocol-relative URL.
        module: Whether to emit <script type="module">.
        loading: Script loading behavior.
        position: Where to inject the script tag.
        attrs: Extra script tag attributes.

    Example:
        ui.add_js_url("https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js")
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")

    asset = JSAsset(
        kind="url",
        source=url,
        module=module,
        loading=loading,
        position=position,
        attrs=attrs or {},
    )

    get_active_assets().js_asset.append(asset)


def add_style_tag(content: str, *, group_id: Optional[str] = None):
    """Add a style tag to the HTML document.

    Args:
        content (str): The content of the style tag.
        group_id (Optional[str], optional): The group id of the style tag. Defaults to None.
    """
    get_active_assets().style_tags.append(StyleTag(content, group_id))


def add_component_dependency(element: type[Element], info: ComponentDependencyInfo):
    get_active_assets().component_dependencies.add(element, info)
    return info


def register_component_extension(
    *,
    target: type[Element],
    kind: str,
    values: list[str],
):
    """
    Invoked by third-party component authors to declare the additional dependencies required for a component family in Zero mode.
    """
    get_active_assets().component_extensions.add(
        target=target,
        kind=kind,
        values=values,
    )
