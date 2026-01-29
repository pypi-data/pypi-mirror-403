from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from instaui.internal.backend.base import BaseBackend
from instaui.internal.backend.invocation import BackendInvocation


class BackendBindingRegistryBase(ABC):
    @abstractmethod
    def register(self, invocation: BackendInvocation) -> int:
        pass

    @abstractmethod
    def register_asset(self, path: Path) -> int:
        pass

    @abstractmethod
    def get_value(self, ref_id: int) -> Any:
        pass


class BackendBindingRegistry(BackendBindingRegistryBase):
    def __init__(self, backend: BaseBackend):
        self.backend = backend
        self._counter = 0
        self._asset_refs: dict[int, Path] = {}
        self._value_map: dict[int, Any] = {}

    def register(self, invocation: BackendInvocation) -> int:
        rid = self._next_id()
        self._value_map[rid] = self.backend.register_invocation(rid, invocation)
        return rid

    def register_asset(self, path: Path) -> int:
        rid = self._next_id()
        self._asset_refs[rid] = path
        return rid

    def get_value(self, ref_id: int) -> Any:
        return self._value_map[ref_id]

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter


class UnboundBackendBindingRegistry(BackendBindingRegistryBase):
    def register(self, invocation: BackendInvocation) -> int:
        raise NotImplementedError

    def register_asset(self, path: Path) -> int:
        raise NotImplementedError

    def get_value(self, ref_id: int) -> Any:
        raise NotImplementedError
