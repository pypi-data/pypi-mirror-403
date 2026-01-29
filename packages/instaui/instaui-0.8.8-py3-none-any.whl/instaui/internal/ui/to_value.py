from typing import TypeVar, cast
from .bindable import VarableBindHelper, BindableMixin
from .app_context import get_current_scope

_TOutput = TypeVar("_TOutput")


class ToValue(BindableMixin):
    def __init__(self, value) -> None:
        self.value = value
        self._bind_helper = VarableBindHelper(
            self,
            define_scope=get_current_scope(),
            lazy_mark_used=[value],
        )

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        pass


def to_value(value: _TOutput) -> _TOutput:
    """
    Converts a reactive state or computed value to a static value.

    Args:
        value (_TOutput): A reactive state or computed value to be converted to its static equivalent.

    Example:
    .. code-block:: python
        org = ui.state("foo")

        # The initial value is "foo", but it will not sync with org.
        other = ui.state(ui.to_value(org))
    """
    return cast(_TOutput, ToValue(value))
