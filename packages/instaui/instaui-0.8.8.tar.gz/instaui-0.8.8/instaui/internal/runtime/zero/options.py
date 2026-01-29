from pathlib import Path
from typing import Callable, Optional, Union
from instaui.cdn.options import CdnResourceOption


class ZeroOptions:
    def __init__(
        self,
        debug: bool = False,
        icons_svg_path: Optional[Union[Path, Callable[[], Path]]] = None,
        cdn_resource_options: Optional[list[CdnResourceOption]] = None,
    ) -> None:
        self.debug = debug
        self.icons_svg_path = icons_svg_path
        self.cdn_resource_options = cdn_resource_options or []

    def get_import_maps_cdn_overrides(self) -> dict[str, str]:
        if not self.cdn_resource_options:
            return {}

        return dict(
            item
            for option in self.cdn_resource_options
            for item in (option.import_maps or {}).items()
        )

    def get_css_links_cdn_overrides(self) -> dict[Path, str]:
        if not self.cdn_resource_options:
            return {}

        return dict(
            item
            for option in self.cdn_resource_options
            for item in (option.css_links or {}).items()
        )
