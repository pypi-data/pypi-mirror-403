from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Protocol
from instaui.protocol.module_import.import_item import PresetProtocol

if TYPE_CHECKING:
    from instaui.internal.ast.core import AppBootstrap


class ImportTableProtocol(Protocol):
    def use(
        self,
        *,
        module: str,
        name: str,
        alias: Optional[str] = None,
    ) -> str: ...

    def use_from_preset(
        self,
        preset: PresetProtocol,
    ) -> str: ...

    def render(self) -> str: ...


class AppBootstrapCodegenProtocol(Protocol):
    def emit(self, bootstrap: AppBootstrap) -> str: ...
