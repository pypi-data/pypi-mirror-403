from instaui.internal.ast.symbol import SymbolId

TOP_LEVEL_VAR_HINT = "_$tlv"
COMPONENT_HINT = "_$cp"
VAR_HINT = "_$v"


class VariableNameContext:
    def __init__(self) -> None:
        # symbol → js name
        self._symbols: dict[SymbolId, str] = {}

        # independent counters
        self._var_counter = 0
        self._component_counter = 0
        self._top_level_var_counter = 0

    # ---------- variables ----------
    def declare_var(self, symbol: SymbolId) -> str:
        if symbol in self._symbols:
            return self._symbols[symbol]

        name = f"{VAR_HINT}{self._var_counter}"
        self._var_counter += 1
        self._symbols[symbol] = name
        return name

    # ---------- components ----------
    def declare_component(self, symbol: SymbolId) -> str:
        if symbol in self._symbols:
            return self._symbols[symbol]

        name = f"{COMPONENT_HINT}{self._component_counter}"
        self._component_counter += 1
        self._symbols[symbol] = name
        return name

    def declare_top_level_var(self, symbol: SymbolId) -> str:
        if symbol in self._symbols:
            return self._symbols[symbol]

        name = f"{TOP_LEVEL_VAR_HINT}{self._top_level_var_counter}"
        self._top_level_var_counter += 1
        self._symbols[symbol] = name
        return name

    # ---------- identifiers ----------
    def resolve(self, symbol: SymbolId) -> str:
        return self._symbols[symbol]
