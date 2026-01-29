from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from instaui.internal.assets.component_extension_registry import (
    ComponentExtensionRegistry,
)
from instaui.systems.dataclass_system import dataclass, field
from .css_assets import CssAssetCollection
from .style_assets import StyleTag
from .component_dep import ComponentDependencyRegistry

if TYPE_CHECKING:
    from .script_assets import JSAsset
    from .plugin import PluginDependencyInfo


@dataclass
class AssetsDeclaration:
    css_links: CssAssetCollection = field(default_factory=CssAssetCollection)
    style_tags: list[StyleTag] = field(default_factory=list)
    js_asset: list[JSAsset] = field(default_factory=list)
    import_maps: dict[str, Union[str, Path]] = field(default_factory=dict)
    favicon: Optional[Union[str, Path]] = field(default=None)
    plugins: set[PluginDependencyInfo] = field(default_factory=set)
    component_dependencies: ComponentDependencyRegistry = field(
        default_factory=ComponentDependencyRegistry
    )
    component_extensions: ComponentExtensionRegistry = field(
        default_factory=ComponentExtensionRegistry
    )

    def clone(self) -> AssetsDeclaration:
        """
        Use only when necessary. Typically, the global and local can be merged via the pipeline.
        """
        import copy

        return copy.deepcopy(self)
