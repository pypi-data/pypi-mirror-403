from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from instaui.internal.backend.invocation import BackendInvocation


class BaseBackend(ABC):
    @abstractmethod
    def register_invocation(
        self, ref_id: int, invocation: BackendInvocation
    ) -> Any: ...


class AssetBackendMixin(ABC):
    @abstractmethod
    def register_asset(self, path: Path) -> str: ...
