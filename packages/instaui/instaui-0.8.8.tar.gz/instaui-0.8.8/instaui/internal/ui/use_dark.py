from __future__ import annotations
from typing import cast

from instaui.constants.ui import INSTAUI_JS_MODULE_NAME, USE_DARK_REF_METHOD
from instaui.debug.api_boundary import user_api
from instaui.internal.ui.custom_var import CustomVar


@user_api
def use_dark() -> bool:
    """
    On start up, it reads the value from localStorage/sessionStorage (the key is configurable) to see if there is a user configured color scheme, if not, it will use users' system preferences.


    Example:
    .. code-block:: python
        from instaui import ui,html

        @ui.page('/')
        def index():
            dark = ui.use_dark()
            html.checkbox(dark)
    """

    return cast(
        bool,
        CustomVar(INSTAUI_JS_MODULE_NAME, USE_DARK_REF_METHOD),
    )
