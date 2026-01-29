from contextlib import contextmanager
from typing import Iterator, Optional
from instaui.internal.ast.core import ComponentDef
from instaui.internal.ast.symbol import SymbolId


class ComponentScope:
    def __init__(self) -> None:
        self._stack: list[ComponentDef] = []

    @contextmanager
    def push(self, comp: ComponentDef) -> Iterator[None]:
        self._stack.append(comp)
        try:
            yield
        finally:
            self._stack.pop()

    @property
    def current(self) -> Optional[ComponentDef]:
        if not self._stack:
            return None
        return self._stack[-1]

    def declare_var(self, symbol: SymbolId) -> None:
        comp = self.current
        if comp is None:
            raise RuntimeError("Variable declared outside component")

        comp.vars.append(symbol)
