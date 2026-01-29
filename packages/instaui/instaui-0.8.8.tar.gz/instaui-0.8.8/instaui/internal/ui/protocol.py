from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instaui.internal.ui.enums import InputBindingType, OutputSetType


class CanInputProtocol(ABC):
    @abstractmethod
    def _to_event_input_type(self) -> InputBindingType:
        pass


class CanOutputProtocol(ABC):
    @abstractmethod
    def _to_event_output_type(self) -> OutputSetType:
        pass


class ObservableProtocol(CanInputProtocol):
    pass
