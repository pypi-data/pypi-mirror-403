from typing import Any, Optional, Union
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.base import ExprBuilderProtocol
from instaui.internal.ui.missing import TMissing
from instaui.internal.ui.pre_setup import PreSetupAction


class PreSetupParser:
    def __init__(self, expr_builder: ExprBuilderProtocol):
        self.expr_builder = expr_builder

    def parse(self, pre_setup: list[list]) -> Optional[expression.ListExpr]:
        if not pre_setup:
            return None

        pre_setup = [
            [
                self.expr_builder.build(target),
                self.parse_item_value(running_value),
                self.parse_item_value(reset_value),
            ]
            for target, running_value, reset_value in pre_setup
        ]

        return expression.ListExpr(
            [
                self.expr_builder.list_shallow(pre_setup_item)
                for pre_setup_item in pre_setup
            ]
        )

    def parse_item_value(
        self, maybe_action: Union[Any, TMissing]
    ) -> expression.Expression:
        if isinstance(maybe_action, TMissing):
            return expression.ObjectLiteral(
                {
                    "type": "missing",
                }
            )

        if isinstance(maybe_action, PreSetupAction):
            return self.expr_builder.object_shallow(
                {
                    "type": "action",
                    "value": expression.ObjectExpr.from_kwargs(
                        **{
                            "inputs": self.expr_builder.list_shallow(
                                maybe_action.inputs
                            )
                            or None,
                            "code": expression.RawFunctionExpr(maybe_action.code),
                        }
                    ),
                }
            )

        return self.expr_builder.object_shallow(
            {"type": "const", "value": self.expr_builder.build(maybe_action)}
        )
