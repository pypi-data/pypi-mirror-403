from __future__ import annotations
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from instaui.internal.ast.core import Render


class RenderEmitter(Protocol):
    def emit_render(self, render: Render) -> str: ...
