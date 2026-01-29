from __future__ import annotations
import inspect
import threading
from typing import TYPE_CHECKING, Callable, Mapping, Optional
from fastapi import Response, APIRouter
from instaui.internal.backend.common import handler as _handler
from instaui.internal.backend.common.event_dataset import event_dataset_type_adapter
from instaui.protocol.codec.type_adapter import TypeAdapterProtocol
from . import _utils

if TYPE_CHECKING:
    from .endpoints import ServerEndpoints


_event_handlers: dict[str, _handler.HandlerInfo] = {}
dict_lock = threading.Lock()


def create_router(router: APIRouter, debug_mode: bool, endpoints: ServerEndpoints):
    _async_handler(router, endpoints)
    _sync_handler(router, endpoints)

    if debug_mode:

        @router.get("/instaui/event-infos", tags=["instaui-debug"])
        def event_infos():
            return _get_statistics_info()


def _async_handler(router: APIRouter, endpoints: ServerEndpoints):
    @router.post(endpoints.ASYNC_EVENT_URL)
    async def _(data: dict, response: Response):
        handler = _get_handler(data)
        if handler is None:
            raise _utils.HandlerNotFoundError("event handler not found")

        assert inspect.iscoroutinefunction(handler.fn), (
            "handler must be a coroutine function"
        )

        result = await handler.fn(*handler.get_handler_args(_get_binds_from_data(data)))
        return _utils.response_web_data(handler.outputs_binding_count, result, response)


def _sync_handler(router: APIRouter, endpoints: ServerEndpoints):
    @router.post(endpoints.EVENT_URL)
    def _(data: dict, response: Response):
        handler = _get_handler(data)
        if handler is None:
            raise _utils.HandlerNotFoundError("event handler not found")

        result = handler.fn(*handler.get_handler_args(_get_binds_from_data(data)))

        return _utils.response_web_data(handler.outputs_binding_count, result, response)


def register_event_handler(
    key: str,
    handler: Callable,
    outputs_binding_count: int,
    dataset_input_indexs: list[int],
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None,
):
    if key in _event_handlers:
        return

    custom_type_adapter_map = dict(custom_type_adapter_map or {}) | {
        i: event_dataset_type_adapter for i in dataset_input_indexs
    }

    with dict_lock:
        _event_handlers[key] = _handler.HandlerInfo.from_handler(
            handler,
            outputs_binding_count,
            custom_type_adapter_map=custom_type_adapter_map,
        )


def _get_handler(data: dict):
    return _event_handlers.get(data["hKey"])


def _get_binds_from_data(data: dict):
    return [bind for bind in data.get("bind", [])]


def _get_statistics_info():
    return {
        "_event_handlers count": len(_event_handlers),
        "_event_handlers keys": list(_event_handlers.keys()),
    }
