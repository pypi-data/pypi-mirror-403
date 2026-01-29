from __future__ import annotations
import threading
from typing import TYPE_CHECKING, Callable, Hashable, Mapping, Optional
from fastapi import APIRouter
from instaui.internal.backend.common import handler as _handler
from instaui.protocol.codec.type_adapter import TypeAdapterProtocol
from . import _utils

if TYPE_CHECKING:
    from .endpoints import ServerEndpoints

_watch_handlers: dict[Hashable, _handler.HandlerInfo] = {}
dict_lock = threading.Lock()


def create_router(router: APIRouter, debug_mode: bool, endpoints: ServerEndpoints):
    _async_handler(router, endpoints)
    _sync_handler(router, endpoints)

    if debug_mode:

        @router.get("/instaui/watch-infos", tags=["instaui-debug"])
        def watch_infos():
            return get_statistics_info()


def _async_handler(router: APIRouter, endpoints: ServerEndpoints):
    @router.post(endpoints.ASYNC_WATCH_URL)
    async def _(data: dict):
        hkey = data.pop("hKey")
        handler_info = _watch_handlers.get(hkey)
        if handler_info is None:
            raise _utils.HandlerNotFoundError("watch handler not found")

        result = await handler_info.fn(
            *handler_info.get_handler_args(_get_binds_from_data(data))
        )
        return _utils.response_web_data(handler_info.outputs_binding_count, result)


def _sync_handler(router: APIRouter, endpoints: ServerEndpoints):
    @router.post(endpoints.WATCH_URL)
    def _(data: dict):
        hkey = data.pop("hKey")
        handler_info = _watch_handlers.get(hkey)
        if handler_info is None:
            raise _utils.HandlerNotFoundError("watch handler not found")

        result = handler_info.fn(
            *handler_info.get_handler_args(_get_binds_from_data(data))
        )
        return _utils.response_web_data(handler_info.outputs_binding_count, result)


def register_watch_handler(
    key: str,
    handler: Callable,
    outputs_binding_count: int,
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None,
):
    if key in _watch_handlers:
        return
    with dict_lock:
        _watch_handlers[key] = _handler.HandlerInfo.from_handler(
            handler, outputs_binding_count, custom_type_adapter_map
        )


def _get_binds_from_data(data: dict):
    return data.get("input", [])


def get_statistics_info():
    return {
        "_watch_handlers count": len(_watch_handlers),
        "_watch_handlers keys": list(_watch_handlers.keys()),
    }
