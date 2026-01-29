from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from .resolver import AssetResolver

if TYPE_CHECKING:
    from instaui.internal.backend.base import AssetBackendMixin


class BackendAssetResolver(AssetResolver):
    def __init__(self, backend: AssetBackendMixin):
        self.backend = backend

    def resolve_asset(self, path: Path) -> str:
        return self.backend.register_asset(path)
