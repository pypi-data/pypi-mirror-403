from instaui.internal.pipeline.assets import (
    AssetsPipeline,
    PluginCssProcessor,
    PluginImportMapProcessor,
    ComponentCssProcessor,
    ComponentImportMapProcessor,
)


WEB_ASSETS_PIPELINE = AssetsPipeline(
    [
        PluginCssProcessor(),
        PluginImportMapProcessor(),
        ComponentCssProcessor(),
        ComponentImportMapProcessor(),
    ]
)
