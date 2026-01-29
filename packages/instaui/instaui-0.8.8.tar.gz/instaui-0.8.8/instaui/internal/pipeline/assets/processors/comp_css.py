from pathlib import Path
from typing import Sequence
from instaui.constants.runtime import RuntimeMode
from instaui.internal.assets.base import AssetsDeclaration
from instaui.internal.assets.component_dep import ComponentDependencyInfo
from instaui.internal.assets.css_assets import CssAsset


class ComponentCssProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for comp in assets.component_dependencies.records:
            for css in comp.dependency.css:
                # CSS resources with component namespaces should not override directly added CSS resources
                if (
                    isinstance(css, CssAsset)
                    and css.namespace is not None
                    and css.namespace in assets.css_links.by_namespace
                ):
                    continue

                assets.css_links.add(css)


class ZeroModeComponentCssProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for record in assets.component_dependencies.records:
            dependency = record.dependency
            css_resources = self._resolve_zero_mode_css(dependency)

            for css in css_resources:
                # CSS resources with component namespaces should not override directly added CSS resources
                if (
                    isinstance(css, CssAsset)
                    and css.namespace is not None
                    and css.namespace in assets.css_links.by_namespace
                ):
                    continue

                assets.css_links.add(css)

    @staticmethod
    def _resolve_zero_mode_css(
        dependency: ComponentDependencyInfo,
    ) -> Sequence[str | Path | CssAsset]:
        """
        CSS selection rules in Zero mode:

        - If `overrides[RuntimeMode.ZERO].zero_css` exists, **use this list exclusively**
        - Otherwise, fall back to `dependency.css`"
        """
        overrides = dependency.overrides
        if not overrides:
            return dependency.css

        zero_override = overrides.get(RuntimeMode.ZERO)
        if not zero_override or not zero_override.zero_css:
            return dependency.css

        return zero_override.zero_css
