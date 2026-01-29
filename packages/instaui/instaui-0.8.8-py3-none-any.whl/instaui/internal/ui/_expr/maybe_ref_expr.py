from __future__ import annotations
from typing import Any
from instaui.internal.ui.bindable import (
    BindableMixin,
    mark_used,
    is_bindable,
    mark_provided,
)


class UIMaybeRefExpr(BindableMixin):
    def __init__(self, value: Any) -> None:
        self.value = value

    @property
    def _used(self) -> bool:
        return self.value._used if is_bindable(self.value) else True

    def _mark_used(self) -> None:
        mark_used(self.value)

    def _mark_provided(self) -> None:
        if is_bindable(self.value):
            mark_provided(self.value)
