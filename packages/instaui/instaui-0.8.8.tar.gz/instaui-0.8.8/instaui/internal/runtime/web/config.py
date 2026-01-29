from pathlib import Path
from typing import Union
from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class WebUserLaunchConfig:
    caller_folder_path: Path
    debug: bool
    use_gzip: Union[int, bool] = True
    prefix: str = ""
    prerender: bool = False
    prerender_concurrency: int = 4
