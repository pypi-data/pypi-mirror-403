from __future__ import annotations
import abc
from typing import TYPE_CHECKING, Optional
from instaui.internal.ui.event import EventMixin
from instaui.internal.ui.event_modifier import TEventModifier


if TYPE_CHECKING:
    from instaui.internal.ui.element import Element


class InputEventMixin:
    @abc.abstractmethod
    def _input_event_mixin_element(self) -> Element:
        pass

    def on_change(
        self,
        handler: EventMixin,
        *,
        params: Optional[list] = None,
        modifier: Optional[list[TEventModifier]] = None,
    ):
        self._input_event_mixin_element().on(
            "change", handler, params=params, modifier=modifier
        )
        return self

    def on_input(
        self,
        handler: EventMixin,
        *,
        params: Optional[list] = None,
        modifier: Optional[list[TEventModifier]] = None,
    ):
        self._input_event_mixin_element().on(
            "input", handler, params=params, modifier=modifier
        )
        return self
