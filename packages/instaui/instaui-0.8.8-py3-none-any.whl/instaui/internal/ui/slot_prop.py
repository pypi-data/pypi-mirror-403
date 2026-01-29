from instaui.internal.ui.app_context import get_current_scope
from instaui.internal.ui.bindable import BindableMixin, VarableBindHelper
from instaui.internal.ui.enums import InputBindingType
from instaui.internal.ui.path_var import PathVar
from instaui.internal.ui.protocol import ObservableProtocol
from instaui.internal.ui.variable import Variable


class SlotProp(
    PathVar,
    Variable,
    ObservableProtocol,
    BindableMixin,
):
    def __init__(self) -> None:
        super().__init__()
        define_scope = get_current_scope()

        self._bind_helper = VarableBindHelper(self, define_scope=define_scope)

    def get(self, name: str):
        return self[name]

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
