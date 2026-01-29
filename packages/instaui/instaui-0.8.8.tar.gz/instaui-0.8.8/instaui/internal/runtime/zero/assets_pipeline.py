from instaui.internal.pipeline.assets import (
    AssetsPipeline,
    PluginCssProcessor,
    PluginImportMapProcessor,
    ZeroModeComponentCssProcessor,
    ZeroModeComponentImportMapProcessor,
    ZeroModeComponentExtensionProcessor,
)


ZERO_ASSETS_PIPELINE = AssetsPipeline(
    [
        PluginCssProcessor(),
        PluginImportMapProcessor(),
        ZeroModeComponentCssProcessor(),
        ZeroModeComponentImportMapProcessor(),
        ZeroModeComponentExtensionProcessor(),
    ]
)
