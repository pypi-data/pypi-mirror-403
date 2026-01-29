from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from instaui.debug.model import SourceSpan


class CodegenError(Exception):
    def __init__(self, message: str, source: SourceSpan | None):
        super().__init__(message)
        self.message = message
        self.source = source

    def __str__(self) -> str:
        if self.source is not None:
            return f"{self.message}\n--> {self.source}"
        return self.message
