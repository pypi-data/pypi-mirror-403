from __future__ import annotations
from typing import Optional
from instaui.constants.runtime import RuntimeMode
from instaui.systems.dataclass_system import (
    dataclass,
    asdict_no_none,
    metadata_key_resolver,
    replace,
    field,
)


@dataclass()
class AppMeta:
    mode: RuntimeMode
    version: str
    debug: bool
    route: Optional[ServerRoute] = None
    server_info: Optional[ServerInfo] = field(
        default=None, metadata={"key": "serverInfo"}
    )
    app_icons: Optional[AppIcons] = field(default=None, metadata={"key": "appIcons"})

    def to_dict(self):
        return asdict_no_none(self, key_resolver=metadata_key_resolver())

    def replace(
        self,
        *,
        app_icons: Optional[AppIcons] = None,
        route: Optional[ServerRoute] = None,
    ):
        return replace(self, app_icons=app_icons, route=route)


@dataclass()
class ServerInfo:
    watch_url: str
    watch_async_url: str
    event_url: str
    event_async_url: str
    download_url: str
    assets_url: str
    assets_icons_name: str


@dataclass()
class ServerRoute:
    path: str


@dataclass()
class AppIcons:
    names: Optional[list[str]] = None
    sets: Optional[list[str]] = None

    def __bool__(self):
        return bool(self.names or self.sets)
