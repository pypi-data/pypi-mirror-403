from typing import Callable
from instaui.internal.ui.bindable import BindableMixin


class UploadEndpoint(BindableMixin):
    def __init__(self, handler: Callable) -> None:
        self.handler = handler

    @property
    def _used(self) -> bool:
        return True

    def _mark_used(self) -> None:
        pass

    def _mark_provided(self) -> None:
        pass
