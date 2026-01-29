from instaui.internal.pipeline.assets import (
    AssetsPipeline,
    PluginCssProcessor,
    PluginImportMapProcessor,
    ComponentCssProcessor,
    ComponentImportMapProcessor,
)


WEBVIEW_ASSETS_PIPELINE = AssetsPipeline(
    [
        PluginCssProcessor(),
        PluginImportMapProcessor(),
        ComponentCssProcessor(),
        ComponentImportMapProcessor(),
    ]
)
