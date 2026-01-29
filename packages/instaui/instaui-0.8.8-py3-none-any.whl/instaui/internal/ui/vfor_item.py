from typing import Generic, TypeVar
from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper
from instaui.internal.ui.enums import InputBindingType, OutputSetType
from instaui.internal.ui.path_var import PathVar
from instaui.internal.ui.protocol import (
    CanOutputProtocol,
    ObservableProtocol,
)
from instaui.internal.ui.variable import Variable


_T = TypeVar("_T")


class VForItem(
    Variable,
    PathVar,
    CanOutputProtocol,
    ObservableProtocol,
    BindableMixin,
    Generic[_T],
):
    def __init__(self):
        super().__init__()
        self._bind_helper = VarableBindHelper(self, define_scope=get_current_scope())

    def __getattr__(self, name: str):
        return self[name]

    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.Ref

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id

    def _is_providable(self) -> bool:
        return False


class VForIndex(
    Variable,
    PathVar,
    ObservableProtocol,
    BindableMixin,
):
    def __init__(self):
        super().__init__()
        self._bind_helper = VarableBindHelper(self, define_scope=get_current_scope())

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _is_providable(self) -> bool:
        return False


class VForItemKey(Variable, PathVar, ObservableProtocol, BindableMixin):
    def __init__(self):
        super().__init__()
        self._bind_helper = VarableBindHelper(self, define_scope=get_current_scope())

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()

    @property
    def _define_scope_id(self) -> int:
        return self._bind_helper._define_scope.id

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _is_providable(self) -> bool:
        return False


TVForItem = VForItem
TVForIndex = VForIndex
