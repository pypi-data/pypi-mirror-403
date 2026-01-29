from instaui.internal.assets.base import AssetsDeclaration


class PluginImportMapProcessor:
    def process(self, assets: AssetsDeclaration) -> None:
        for plugin in assets.plugins:
            for k, v in plugin.externals.items():
                assets.import_maps.setdefault(k, v)
