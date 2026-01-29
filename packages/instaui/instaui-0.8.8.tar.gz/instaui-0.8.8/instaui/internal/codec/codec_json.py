from __future__ import annotations
import inspect
from typing import Any, Callable, Sequence
from pydantic import TypeAdapter, RootModel

from instaui.protocol.codec.type_adapter import TypeAdapterProtocol


JSONValue = Any  # dict | list | str | int | float | bool | None


class JsonCodec:
    def __init__(self) -> None:
        self._type_adapter_cache: dict[type, TypeAdapterProtocol] = {}

    def python_to_json_value(self, value: Any) -> JSONValue:
        return RootModel(value).model_dump()

    def build_type_adapter_map(
        self, func: Callable, inputs: Sequence
    ) -> dict[int, Callable[[Any], Any]] | None:
        if not inputs:
            return None

        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        adapter_map: dict[int, Callable[[Any], Any]] = {}

        for idx, (param, _) in enumerate(zip(params, inputs)):
            annotation = param.annotation

            if annotation is inspect._empty:
                continue

            adapter_validator = self._get_type_adapter_validator(annotation)
            adapter_map[idx] = adapter_validator

        return adapter_map

    def _get_type_adapter_validator(self, tp: type) -> TypeAdapterProtocol:
        if tp not in self._type_adapter_cache:
            adapter = TypeAdapter(tp)
            self._type_adapter_cache[tp] = lambda value: adapter.validate_python(value)
        return self._type_adapter_cache[tp]


json_codec = JsonCodec()


def python_to_json_value(value: Any) -> JSONValue:
    return json_codec.python_to_json_value(value)


def build_type_adapter_map(
    func: Callable, inputs: Sequence
) -> dict[int, Callable[[Any], Any]] | None:
    return json_codec.build_type_adapter_map(func, inputs)


class JsonCodecError(TypeError):
    pass
