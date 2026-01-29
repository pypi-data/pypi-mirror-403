from instaui.internal.backend.common.response import response_data
from .watch_handler import get_watch_handler
from .event_handler import get_event_handler


class Api:
    def watch_call(self, data: dict):
        hkey = data.pop("hKey")
        handler_info = get_watch_handler(hkey)
        if handler_info is None:
            return {"error": "watch handler not found"}

        result = handler_info.fn(
            *handler_info.get_handler_args(_get_binds_from_data(data))
        )
        return response_data(handler_info.outputs_binding_count, result)

    def event_call(self, data: dict):
        hkey = data.pop("hKey")
        handler = get_event_handler(hkey)
        if handler is None:
            raise ValueError("event handler not found")

        args = [bind for bind in data.get("bind", [])]

        result = handler.fn(*handler.get_handler_args(args))
        return response_data(handler.outputs_binding_count, result)


def _get_binds_from_data(data: dict):
    return data.get("input", [])
