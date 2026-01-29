from pathlib import Path
from typing import Mapping
from instaui.constants.runtime import RuntimeMode
from instaui.internal.assets.base import AssetsDeclaration
from instaui.internal.assets.component_dep import ComponentDependencyInfo


class ComponentImportMapProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for comp in assets.component_dependencies.records:
            for k, v in comp.dependency.externals.items():
                assets.import_maps.setdefault(k, v)


class ZeroModeComponentImportMapProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for record in assets.component_dependencies.records:
            dependency = record.dependency

            externals = self._resolve_zero_mode_externals(dependency)

            for key, path in externals.items():
                assets.import_maps.setdefault(key, path)

    @staticmethod
    def _resolve_zero_mode_externals(
        dependency: ComponentDependencyInfo,
    ) -> Mapping[str, Path]:
        overrides = dependency.overrides
        if not overrides:
            return dependency.externals

        zero_override = overrides.get(RuntimeMode.ZERO)
        if not zero_override or not zero_override.zero_externals:
            return dependency.externals

        return zero_override.zero_externals
