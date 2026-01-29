from abc import ABC, abstractmethod
from typing import Any, Callable, Mapping, Optional, Sequence, Union
from typing_extensions import TypeIs
import types

from instaui.internal.ui.variable import Variable
from instaui.internal.ui._scope import Scope
from instaui.internal.ui.app_context import get_current_scope


class BindableMixin(ABC):
    @property
    @abstractmethod
    def _used(self) -> bool: ...

    @abstractmethod
    def _mark_used(self) -> None: ...

    @abstractmethod
    def _mark_provided(self) -> None: ...


def is_bindable(obj: Any) -> TypeIs[BindableMixin]:
    return isinstance(obj, BindableMixin)


class VarableBindHelper:
    def __init__(
        self,
        owner: Any,
        scope_register_fn: Optional[Callable[[Any], None]] = None,
        *,
        maybe_provides: Optional[Sequence[Union[Variable, Any]]] = None,
        define_scope: Scope,
        on_register_fn: Optional[Callable[..., Any]] = None,
        lazy_mark_used: Optional[Sequence[Any]] = None,
    ):
        self._lazy_mark_used = lazy_mark_used or []
        self.maybe_provides = list(maybe_provides or ()) + [owner]

        def on_mark_used(owner: Any):
            if lazy_mark_used:
                for item in lazy_mark_used:
                    mark_used(
                        item()
                        if callable(item) and isinstance(item, types.FunctionType)
                        else item
                    )
            if scope_register_fn:
                scope_register_fn(owner)

            if on_register_fn:
                on_register_fn()

        self._on_mark_used = on_mark_used
        self._define_scope = define_scope
        self._owner = owner
        self._used = False

    @property
    def used(self) -> bool:
        return self._used

    def _try_injection(self):
        current_scope = get_current_scope()
        for target in self.maybe_provides:
            if isinstance(target, Variable):
                if current_scope is not self._define_scope:
                    if target._is_providable():
                        self._define_scope.provide(target)
                    current_scope.inject(target)

    def mark_used(self):
        self._try_injection()

        if self._used:
            return
        self._used = True
        if self._on_mark_used is not None:
            try:
                self._on_mark_used(self._owner)
            except Exception:
                raise

    def mark_provided(self):
        self._define_scope.provide(self._owner)


def mark_used(obj: Any, *, host_scope_id: Optional[int] = None):
    if isinstance(obj, (list, tuple)):
        for item in obj:
            mark_used(item, host_scope_id=host_scope_id)
    elif isinstance(obj, Mapping):
        for value in obj.values():
            mark_used(value, host_scope_id=host_scope_id)
    elif is_bindable(obj):
        if (
            host_scope_id is not None
            and isinstance(obj, Variable)
            and obj._define_scope_id > host_scope_id
        ):
            raise ValueError("Variable definition cannot be bound to an outer scope.")

        obj._mark_used()
    else:
        pass


def mark_provided(obj: BindableMixin):
    obj._mark_provided()
