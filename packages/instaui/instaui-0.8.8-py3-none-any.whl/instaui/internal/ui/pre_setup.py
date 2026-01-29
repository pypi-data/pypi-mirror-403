from typing import Optional, Sequence

from instaui.internal.ui._expr.literal_expr import UILiteralExpr


class PreSetupAction:
    def __init__(
        self,
        *,
        code: str,
        inputs: Optional[Sequence] = None,
    ):
        self.type = "action"
        self.inputs = UILiteralExpr.try_parse_list(inputs or [])
        self.code = code


def normalize_pre_setup(pre_setup: list) -> list:
    if not pre_setup:
        return pre_setup
    first = pre_setup[0]
    # e.g [ref, True, False]
    if not isinstance(first, list):
        pre_setup = [pre_setup]

    # e.g [[ref, True, False], [ref2, False, True]]
    return [
        [x[0], UILiteralExpr.try_parse(x[1]), UILiteralExpr.try_parse(x[2])]
        for x in pre_setup
    ]
