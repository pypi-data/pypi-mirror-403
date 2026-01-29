from typing import Optional
from instaui.internal.backend.binding import (
    BackendBindingRegistryBase,
    UnboundBackendBindingRegistry,
)


class RuntimeContext:
    def __init__(
        self, *, binding_registry: Optional[BackendBindingRegistryBase] = None
    ):
        self.binding_registry: BackendBindingRegistryBase = (
            binding_registry or UnboundBackendBindingRegistry()
        )
