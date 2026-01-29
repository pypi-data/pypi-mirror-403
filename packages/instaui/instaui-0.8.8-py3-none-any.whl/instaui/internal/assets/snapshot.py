from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from instaui.systems.dataclass_system import dataclass

if TYPE_CHECKING:
    from .plugin import PluginDependencyInfo
    from instaui.internal.assets.style_assets import StyleTag


@dataclass(frozen=True)
class AssetsSnapshot:
    css_links: list[str | Path]
    style_tags: list[StyleTag]
    script_tags_in_head: list[ScriptTagSnapshot]
    script_tags_in_body: list[ScriptTagSnapshot]
    import_maps: dict[str, str | Path]
    favicon: Optional[str | Path]
    plugins: set[PluginDependencyInfo]
    component_dependencies: list[ComponentDependencySnapshot]


@dataclass(frozen=True)
class ComponentDependencySnapshot:
    tag: str
    esm: Path


@dataclass(frozen=True)
class ScriptTagSnapshot:
    inline_code: str | None = None
    attrs: dict[str, Any] | None = None
