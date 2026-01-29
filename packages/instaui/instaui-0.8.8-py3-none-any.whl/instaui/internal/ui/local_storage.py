from typing import TypeVar, cast
from instaui.constants.ui import STORAGE_REF_METHOD, INSTAUI_JS_MODULE_NAME
from instaui.debug.api_boundary import user_api
from instaui.internal.ui.custom_var import CustomVar

_T = TypeVar("_T")


@user_api
def local_storage(key: str, value: _T, deep_compare: bool = False) -> _T:
    """
    Creates a reactive state object synchronized with the browser's local storage.

    This function initializes a reactive value tied to a given key in local storage.
    The state persists across page reloads and retains its value between sessions
    on the same browser and device.

    Args:
        key (str): The local storage key to associate with the value.
        value (_T): The default value to use if no value exists in local storage.

    Returns:
        _T: A reactive value linked to the specified local storage key.

    Example:
    .. code-block:: python

        from instaui import ui, html

        @ui.page('/')
        def index():
            name = ui.local_storage("username", "")
            html.input(name)
    """

    if isinstance(value, CustomVar):
        return value

    return cast(
        _T,
        CustomVar(
            INSTAUI_JS_MODULE_NAME,
            STORAGE_REF_METHOD,
            args={"type": "local", "key": key, "value": value},
            deep_compare=deep_compare,
        ),
    )
