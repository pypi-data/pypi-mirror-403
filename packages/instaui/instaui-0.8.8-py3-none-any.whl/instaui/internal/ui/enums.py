from __future__ import annotations
from enum import IntEnum


class InputBindingType(IntEnum):
    Ref = 0
    EventContext = 1
    Data = 2
    JsFn = 3
    ElementRef = 4
    EventContextDataset = 5


class OutputSetType(IntEnum):
    Ref = 0
    RouterAction = 1
    ElementRefAction = 2
    JsCode = 3
    FileDownload = 4
