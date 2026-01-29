from typing import Callable, Mapping, Optional
from instaui.internal.backend.common import handler as _handler
from instaui.internal.backend.common.event_dataset import event_dataset_type_adapter
from instaui.protocol.codec.type_adapter import TypeAdapterProtocol


_event_handlers: dict[str, _handler.HandlerInfo] = {}


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

    _event_handlers[key] = _handler.HandlerInfo.from_handler(
        handler,
        outputs_binding_count,
        custom_type_adapter_map=custom_type_adapter_map,
    )


def get_event_handler(key: str):
    return _event_handlers.get(key)
