from typing import Hashable, Mapping, Optional, Sequence
from instaui.protocol.codec.type_adapter import TypeAdapterProtocol
from instaui.systems.dataclass_system import dataclass


class InvocationSpec:
    """Marker base class for typed invocation specs."""

    pass


@dataclass(frozen=True)
class ComputedSpec(InvocationSpec):
    outputs_binding_count: int
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None
    extra_key: Sequence[Hashable] | None = None


@dataclass(frozen=True)
class WatchSpec(InvocationSpec):
    outputs_binding_count: int
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None
    extra_key: Sequence[Hashable] | None = None


@dataclass(frozen=True)
class EventSpec(InvocationSpec):
    outputs_binding_count: int
    dataset_input_indexs: list[int]
    custom_type_adapter_map: Optional[Mapping[int, TypeAdapterProtocol]] = None
    extra_key: Sequence[Hashable] | None = None
