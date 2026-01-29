from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from instaui.internal.codegen.components.codegen_components import CodegenComponents


if TYPE_CHECKING:
    from instaui.internal.backend.binding import BackendBindingRegistryBase


class CodegenRootContext:
    def __init__(
        self,
        *,
        binding_registry: BackendBindingRegistryBase,
        components: Optional[CodegenComponents] = None,
    ):
        self.binding_registry = binding_registry
        self.components = components or CodegenComponents.default()
