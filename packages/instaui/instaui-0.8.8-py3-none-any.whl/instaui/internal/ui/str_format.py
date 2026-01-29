from typing import cast

from instaui.internal.ui._expr.literal_expr import UILiteralExpr
from .bindable import VarableBindHelper, BindableMixin
from .app_context import get_current_scope


class StrFormat(BindableMixin):
    def __init__(self, template: str, *args, **kwargs) -> None:
        self.template = UILiteralExpr.try_parse(template)
        self.args = list(UILiteralExpr.try_parse(arg) for arg in args)
        self.kwargs = {
            key: UILiteralExpr.try_parse(value) for key, value in kwargs.items()
        }

        self._bind_helper = VarableBindHelper(
            self,
            define_scope=get_current_scope(),
            lazy_mark_used=[
                template,
                args,
                kwargs,
            ],
        )

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()


def str_format(template: str, *args, **kwargs) -> str:
    """
    Formats a string template with positional and keyword arguments.

    Args:
        template (str): The string template containing {} placeholders for formatting.
        *args: Variable length positional arguments for positional formatting.
        **kwargs: Arbitrary keyword arguments for named formatting.

    Example:
    .. code-block:: python
        # Positional formatting
        ui.str_format("pos:a={},b={}", a, b)

        # Index-based positional formatting
        ui.str_format("num pos:a={0},b={1}", a, b)

        # Named formatting
        ui.str_format("name pos:b={b},a={a}", a=a, b=b)
    """
    return cast(str, StrFormat(template, *args, **kwargs))
