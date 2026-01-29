from __future__ import annotations
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import FastAPI
from instaui.systems.dataclass_system import dataclass, field


@dataclass(frozen=True)
class WebUserRunOptions:
    app_hooks: list[Callable[[FastAPI], None]] = field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 8080
    reload: bool = True
    reload_dirs: str = "."
    reload_includes: str = "*.py"
    reload_excludes: str = ".*, .py[cod], .sw.*, ~*"
    log_level: str = "info"
    workers: Optional[int] = None
    uds: Optional[str] = None
    kwargs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WebUserRunWithOptions:
    app: FastAPI
    app_hooks: list[Callable[[FastAPI], None]] = field(default_factory=list)
    tags: Optional[list[str | Enum]] = None
    dependencies: Optional[list[Any]] = None
    responses: Optional[dict[int | str, dict[str, Any]]] = None
