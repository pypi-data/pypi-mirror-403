from enum import Enum


class SymbolKind(str, Enum):
    COMPONENT = "component"
    VAR = "var"
    TOP_LEVEL_VAR = "top_level_var"
