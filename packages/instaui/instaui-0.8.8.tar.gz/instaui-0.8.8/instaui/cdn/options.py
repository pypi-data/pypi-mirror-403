from pathlib import Path
from typing import Optional
from instaui.systems.dataclass_system import dataclass


@dataclass()
class CdnResourceOption:
    import_maps: Optional[dict[str, str]] = None
    css_links: Optional[dict[Path, str]] = None
