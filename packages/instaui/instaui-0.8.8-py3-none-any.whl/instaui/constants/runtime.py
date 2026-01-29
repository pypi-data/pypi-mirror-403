from enum import Enum


class RuntimeMode(str, Enum):
    WEB = "web"
    WEBVIEW = "webview"
    ZERO = "zero"
