from typing import Any, Optional
from instaui.internal.ast.symbol import SymbolId


class IdGenerator:
    def __init__(self, start_id: int = 1) -> None:
        self._next_uid = start_id

    def next_id(self) -> int:
        uid = self._next_uid
        self._next_uid += 1
        return uid


class SymbolMapper:
    def __init__(self, id_generator: Optional[IdGenerator] = None) -> None:
        self._id_generator = id_generator or IdGenerator()
        self._mapping: dict[Any, SymbolId] = {}

    def get_or_create_id(self, obj: Any) -> SymbolId:
        sid = self._mapping.get(obj)
        if sid is None:
            sid = self._new_symbol()
            self._mapping[obj] = sid
        return sid

    def get_id(self, obj: Any) -> Optional[SymbolId]:
        return self._mapping.get(obj)

    def _new_symbol(self) -> SymbolId:
        uid = self._id_generator.next_id()
        return SymbolId(uid)
