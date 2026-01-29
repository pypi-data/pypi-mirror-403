from __future__ import annotations
from typing import TYPE_CHECKING
from instaui.systems.dataclass_system import dataclass

if TYPE_CHECKING:
    from instaui.internal.ast import expression


class PropertyKey:
    pass


@dataclass(frozen=True)
class StringKey(PropertyKey):
    value: str


@dataclass(frozen=True)
class ExpressionKey(PropertyKey):
    expr: expression.Expression
