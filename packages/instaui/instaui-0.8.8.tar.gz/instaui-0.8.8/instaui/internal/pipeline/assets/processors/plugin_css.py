from instaui.internal.assets.base import AssetsDeclaration
from instaui.internal.assets.css_assets import CssAsset


class PluginCssProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for plugin in assets.plugins:
            for css in plugin.css:
                # CSS resources with plugin namespaces should not override directly added CSS resources
                if (
                    isinstance(css, CssAsset)
                    and css.namespace is not None
                    and css.namespace in assets.css_links.by_namespace
                ):
                    continue

                assets.css_links.add(css)
