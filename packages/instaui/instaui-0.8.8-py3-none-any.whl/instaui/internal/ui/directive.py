from __future__ import annotations

from typing import Any, Optional
from .bindable import mark_used


class Directive:
    def __init__(
        self,
        *,
        is_sys: bool,
        name: str,
        arg: Optional[str] = None,
        modifiers: Optional[list[Any]] = None,
        value: Optional[Any] = None,
    ) -> None:
        super().__init__()
        mark_used(value)
        self.name = name
        self._arg = arg
        self._is_sys = is_sys
        self._modifiers = modifiers
        self._value = value

    def __hash__(self) -> int:
        return hash(f"{self.name}:{self._arg}:{self._modifiers}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Directive):
            return False
        return (
            self.name == other.name
            and self._arg == other._arg
            and self._modifiers == other._modifiers
        )
