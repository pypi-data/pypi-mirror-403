from typing import Callable, Hashable, Mapping, Optional
from instaui.internal.backend.common import handler as _handler
from instaui.protocol.codec.type_adapter import TypeAdapterProtocol


_watch_handlers: dict[Hashable, _handler.HandlerInfo] = {}


def register_watch_handler(
    key: str,
    handler: Callable,
    outputs_binding_count: int,
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None,
):
    if key in _watch_handlers:
        return

    _watch_handlers[key] = _handler.HandlerInfo.from_handler(
        handler, outputs_binding_count, custom_type_adapter_map
    )


def get_watch_handler(key: str):
    return _watch_handlers.get(key)
