from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Union
from instaui.systems.dataclass_system import dataclass


class PageBuildStrategy(Enum):
    LAZY = "lazy"
    EAGER = "eager"


@dataclass(frozen=True)
class WebViewUserLaunchConfig:
    assets_path: Path
    debug: bool
    title: str = "InstaUI"
    auto_create_window: Union[bool, str] = "/"
    on_page_mounted: Optional[Callable] = None
    clean_assets_on_start: bool = True
    page_build_strategy: PageBuildStrategy = PageBuildStrategy.LAZY
    prebuild_routes: Optional[list[str]] = None
