from __future__ import annotations
from typing import Callable
from instaui.systems.dataclass_system import dataclass, field


@dataclass()
class CodegenResult:
    code: str
    watch_handlers: list[WatchHandler] = field(default_factory=list)
    event_handlers: list[EventHandler] = field(default_factory=list)
    file_upload_handlers: list[FileUploadHandler] = field(default_factory=list)


@dataclass()
class WatchHandler:
    key: str
    fn: Callable
    output_count: int


@dataclass()
class EventHandler:
    key: str
    fn: Callable
    output_count: int
    dataset_input_indexs: list[int] = field(default_factory=list)


@dataclass()
class FileUploadHandler:
    key: str
    fn: Callable
