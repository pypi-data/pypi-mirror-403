from typing import Optional, cast
from instaui.constants.ui import INSTAUI_JS_MODULE_NAME, USE_PAGE_TITLE_METHOD
from instaui.debug.api_boundary import user_api
from instaui.internal.ui.custom_var import CustomVar


@user_api
def use_page_title(title: Optional[str] = None) -> str:
    """Set the title of the HTML document.

    Args:
        title (str): The title of the HTML document.
    """

    if isinstance(title, CustomVar):
        return title

    return cast(
        str, CustomVar(INSTAUI_JS_MODULE_NAME, USE_PAGE_TITLE_METHOD, args=(title,))
    )
