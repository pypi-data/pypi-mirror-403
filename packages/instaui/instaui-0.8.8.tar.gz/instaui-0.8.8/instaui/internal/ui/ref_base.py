from typing import Any, Optional
from instaui.internal.ui._expr.codec_expr import DataCodecExpr
from instaui.internal.ui.protocol import CanOutputProtocol, ObservableProtocol
from instaui.debug.source import get_source_span
from .app_index import new_scope_if_needed
from .variable import Variable
from .enums import InputBindingType, OutputSetType
from .path_var import PathVar
from .missing import MISSING
from .bindable import BindableMixin, VarableBindHelper
from .app_context import get_current_scope


class RefBase(
    PathVar,
    Variable,
    ObservableProtocol,
    CanOutputProtocol,
    BindableMixin,
):
    def __init__(
        self,
        *,
        value: Optional[Any] = MISSING,
        deep_compare: bool = False,
    ) -> None:
        self._source_span_ = get_source_span()
        new_scope_if_needed()
        define_scope = get_current_scope()
        self._bind_helper = VarableBindHelper(
            self,
            define_scope.register_ref,
            define_scope=define_scope,
            lazy_mark_used=[value],
        )

        self._org_value = value.value if isinstance(value, DataCodecExpr) else value
        self._value = value
        self._deep_compare = deep_compare

    def initial(self) -> Any:
        return self._org_value

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.Ref

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
