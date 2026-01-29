from .bindable import BindableMixin
from .enums import InputBindingType
from .protocol import CanInputProtocol


class EventContext(CanInputProtocol, BindableMixin):
    def __init__(
        self, path: str, *, input_type: InputBindingType = InputBindingType.EventContext
    ):
        self.path = path
        self._input_type = input_type

    @staticmethod
    def dataset(name="eventData"):
        return EventContext(
            f":e=> e.target.dataset.{name}",
            input_type=InputBindingType.EventContextDataset,
        )

    @staticmethod
    def args():
        return EventContext(":(...e)=> e")

    @staticmethod
    def e():
        return EventContext(":e => e")

    @staticmethod
    def target_value():
        return EventContext(":e => e.target.value")

    def _to_event_input_type(self) -> InputBindingType:
        return self._input_type

    @property
    def _used(self) -> bool:
        return True

    def _mark_used(self) -> None:
        pass

    def _mark_provided(self) -> None:
        pass


class DatasetEventContext(CanInputProtocol):
    def __init__(self, event_context: EventContext) -> None:
        self._event_context = event_context

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.EventContextDataset
