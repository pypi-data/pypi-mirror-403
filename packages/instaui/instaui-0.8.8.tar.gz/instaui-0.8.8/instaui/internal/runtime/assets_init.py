from instaui import resources
from instaui.internal.assets.context import GLOBAL_ASSETS

_FRAMEWORK_BOOTSTRAPPED = False


def inject_framework_assets() -> None:
    """Inject framework assets into the assets pool."""

    global _FRAMEWORK_BOOTSTRAPPED
    if _FRAMEWORK_BOOTSTRAPPED:
        return

    GLOBAL_ASSETS.import_maps.update(
        {
            "vue": resources.VUE_ES_JS_PATH,
            "instaui": resources.APP_ES_JS_PATH,
        }
    )

    GLOBAL_ASSETS.css_links.add(resources.APP_CSS_PATH)

    _FRAMEWORK_BOOTSTRAPPED = True
