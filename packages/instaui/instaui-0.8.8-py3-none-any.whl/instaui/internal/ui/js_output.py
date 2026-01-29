from instaui.internal.ui.enums import OutputSetType
from instaui.internal.ui.protocol import CanOutputProtocol


class JsOutput(CanOutputProtocol):
    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.JsCode
