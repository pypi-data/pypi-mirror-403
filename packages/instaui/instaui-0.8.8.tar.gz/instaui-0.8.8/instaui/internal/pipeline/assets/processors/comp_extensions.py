from __future__ import annotations
from typing import TYPE_CHECKING
from instaui.internal.assets.base import AssetsDeclaration

if TYPE_CHECKING:
    from instaui.internal.ui.element import Element


class ZeroModeComponentExtensionProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        used_components = {
            record.component for record in assets.component_dependencies.records
        }

        for target_cls, extensions in assets.component_extensions.items():
            if not any(issubclass(used, target_cls) for used in used_components):
                continue

            self._materialize_extensions(target_cls, extensions, assets)

    def _materialize_extensions(
        self,
        target_cls: type[Element],
        extensions: dict[str, set[str]],
        assets: AssetsDeclaration,
    ):
        resolver = self._get_extension_resolver(target_cls)
        if resolver is None:
            return

        resolver.resolve_zero_extensions(extensions, assets)

    def _get_extension_resolver(self, target_cls):
        return getattr(target_cls, "__zero_extension_resolver__", None)
