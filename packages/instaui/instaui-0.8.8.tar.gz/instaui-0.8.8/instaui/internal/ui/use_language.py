from typing import cast
from instaui.constants.ui import INSTAUI_JS_MODULE_NAME, USE_LANGUAGE_METHOD
from instaui.debug.api_boundary import user_api
from instaui.internal.ui.custom_var import CustomVar


@user_api
def use_language() -> str:
    """
    This function returns the current application's language setting, making it convenient to provide a unified language configuration for surrounding frameworks.
    """

    return cast(
        str,
        CustomVar(INSTAUI_JS_MODULE_NAME, USE_LANGUAGE_METHOD),
    )
