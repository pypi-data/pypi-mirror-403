from typing import TypeVar, cast
from instaui.constants.ui import (
    USE_ROUTE_PARAM_METHOD,
    USE_QUERY_PARAM_METHOD,
    INSTAUI_JS_MODULE_NAME,
)
from instaui.internal.ui.custom_var import CustomVar

_T = TypeVar("_T")


def route_param(name: str, *, default: _T = None) -> _T:
    return cast(
        _T,
        CustomVar(INSTAUI_JS_MODULE_NAME, USE_ROUTE_PARAM_METHOD, args=(name, default)),
    )


def query_param(name: str, *, default: _T = None) -> _T:
    return cast(
        _T,
        CustomVar(INSTAUI_JS_MODULE_NAME, USE_QUERY_PARAM_METHOD, args=(name, default)),
    )
