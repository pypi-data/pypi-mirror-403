from __future__ import annotations
from typing import Any, Mapping, Sequence
from instaui.systems.dataclass_system import dataclass


@dataclass(eq=False)
class UILiteralExpr:
    value: Any

    @classmethod
    def try_parse(cls, value: Any):
        if (
            isinstance(value, (int, float, str, bool, list, dict, tuple))
            or value is None
        ):
            return UILiteralExpr(value)

        return value

    @staticmethod
    def try_parse_list(value: Sequence) -> list:
        return [UILiteralExpr.try_parse(x) for x in value]

    @staticmethod
    def try_parse_dict(value: Mapping) -> dict:
        return {k: UILiteralExpr.try_parse(v) for k, v in value.items()}
