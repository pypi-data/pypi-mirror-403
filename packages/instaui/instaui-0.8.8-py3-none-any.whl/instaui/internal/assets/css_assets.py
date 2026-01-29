from __future__ import annotations
from enum import Enum, IntEnum
from pathlib import Path
from typing import Iterable, Optional, Union, Hashable
from instaui.systems.dataclass_system import dataclass, field
from itertools import chain


class CssRole(str, Enum):
    BASE = "base"  # plugin/reset/default
    COMPONENT = "component"  # regular component (default)
    THEME = "theme"  # theme
    OVERRIDE = "override"  # user override


class _CssLayer(IntEnum):
    BASE = 10
    COMPONENT = 20
    THEME = 30
    OVERRIDE = 40


ROLE_TO_LAYER: dict[CssRole, _CssLayer] = {
    CssRole.BASE: _CssLayer.BASE,
    CssRole.COMPONENT: _CssLayer.COMPONENT,
    CssRole.THEME: _CssLayer.THEME,
    CssRole.OVERRIDE: _CssLayer.OVERRIDE,
}


@dataclass(frozen=True)
class CssAsset:
    path_or_url: Union[Path, str]
    role: CssRole = CssRole.COMPONENT
    namespace: Optional[Hashable] = None

    @property
    def layer(self) -> _CssLayer:
        return ROLE_TO_LAYER[self.role]

    @property
    def is_local(self) -> bool:
        return isinstance(self.path_or_url, Path)

    def __hash__(self) -> int:
        """
        Anonymous assets need deduplication based on:
        - Same path_or_url
        - Same role
        - Same namespace
        """
        return hash((self.path_or_url, self.role, self.namespace))


@dataclass
class CssAssetCollection:
    by_namespace: dict[Hashable, CssAsset] = field(default_factory=dict)
    anonymous: list[CssAsset] = field(default_factory=list)

    def add(
        self,
        css: Union[Path, str, CssAsset],
        *,
        role: CssRole = CssRole.COMPONENT,
        namespace: Optional[Hashable] = None,
    ):
        if isinstance(css, CssAsset):
            asset = css
        else:
            asset = CssAsset(
                path_or_url=css,
                role=role,
                namespace=namespace,
            )

        if asset.namespace is not None:
            # namespace：override
            self.by_namespace[asset.namespace] = asset
        else:
            # anonymous：duplicate removal + order preservation
            if asset not in self.anonymous:
                self.anonymous.append(asset)

    def remove(
        self,
        css: Union[Path, str, CssAsset],
        *,
        role: CssRole = CssRole.COMPONENT,
        namespace: Optional[Hashable] = None,
    ) -> None:
        if isinstance(css, CssAsset):
            asset = css
        else:
            asset = CssAsset(
                path_or_url=css,
                role=role,
                namespace=namespace,
            )

        if asset.namespace is not None:
            self.by_namespace.pop(asset.namespace, None)
        else:
            try:
                self.anonymous.remove(asset)
            except ValueError:
                pass

    def iter_assets(self) -> Iterable[CssAsset]:
        """
        Returns CssAssets for HTML rendering (sorted by layer)
        """
        assets = chain(self.anonymous, self.by_namespace.values())
        assets = sorted(assets, key=lambda a: a.layer)
        return assets

    def iter_css_links(self) -> Iterable[Union[Path, str]]:
        for asset in self.iter_assets():
            yield asset.path_or_url

    @classmethod
    def merge(
        cls,
        global_assets: CssAssetCollection,
        local_assets: CssAssetCollection,
    ) -> CssAssetCollection:
        """
        Merge semantics:
        - Global assets added first
        - Local assets added after
        - Namespace automatically overridden by local
        - Order determined solely by role/layer
        """
        result = cls()

        for asset in global_assets.iter_assets():
            result.add(asset)

        for asset in local_assets.iter_assets():
            result.add(asset)

        return result
