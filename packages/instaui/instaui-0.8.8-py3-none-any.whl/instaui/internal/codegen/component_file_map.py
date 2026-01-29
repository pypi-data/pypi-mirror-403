from __future__ import annotations
from instaui.internal.ast.symbol import SymbolId


class ComponentFileMap:
    def __init__(self) -> None:
        self._map: dict[SymbolId, str] = {}

    def register(self, symbol: SymbolId, path: str) -> None:
        self._map[symbol] = path

    def resolve(self, symbol: SymbolId) -> str:
        return self._map[symbol]
