from __future__ import annotations
from typing import Any, Callable, Iterable, Union
from typing_extensions import TypedDict
import webview.http as http
from webview.guilib import GUIType
from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class WebViewUserRunOptions:
    webview_start_args: WebviewStartArgs


class WebviewStartArgs(TypedDict, total=False):
    func: Union[Callable[..., None], None]
    args: Union[Iterable[Any], None]
    localization: dict[str, str]
    gui: Union[GUIType, None]
    http_server: bool
    http_port: Union[int, None]
    user_agent: Union[str, None]
    private_mode: bool
    storage_path: Union[str, None]
    menu: list[Any]
    server: type[http.ServerType]  # type: ignore
    server_args: dict[Any, Any]
    ssl: bool
    icon: Union[str, None]
