from abc import ABC, abstractmethod
import typing

from .event_modifier import TEventModifier


class EventMixin(ABC):
    @abstractmethod
    def _attach_to_element(
        self,
        *,
        params: typing.Optional[typing.Sequence],
        modifier: typing.Optional[typing.Sequence[TEventModifier]] = None,
    ):
        pass
