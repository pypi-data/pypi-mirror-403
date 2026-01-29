from typing import Optional, Sequence
from instaui.internal.ui.protocol import CanOutputProtocol


def ensure_output_list(outputs: Optional[Sequence] = None):
    if outputs is None:
        return

    for output in outputs:
        if not isinstance(output, CanOutputProtocol):
            raise TypeError("The outputs parameter must be a `ui.state`")
