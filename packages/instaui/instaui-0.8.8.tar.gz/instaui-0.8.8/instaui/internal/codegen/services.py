from __future__ import annotations
from typing import Callable
from abc import ABC, abstractmethod
from pathlib import Path


class JsCodegenServices(ABC):
    @abstractmethod
    def path_map_url(self, path: Path) -> str: ...

    @abstractmethod
    def register_watch_handler(self, key: str, fn: Callable, output_count: int): ...

    @abstractmethod
    def register_event_handler(
        self, key: str, fn: Callable, output_count: int, dataset_input_indexs: list[int]
    ): ...

    @abstractmethod
    def resolve_upload_url(self, key: str, handler: Callable) -> str: ...
