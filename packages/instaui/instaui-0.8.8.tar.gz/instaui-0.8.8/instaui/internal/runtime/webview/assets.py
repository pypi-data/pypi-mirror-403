from pathlib import Path
import shutil
from instaui.internal.pipeline.asset_resolver.webview_resolver import AssetMaterializer
from instaui.internal.runtime.utils import path_utils
from instaui.systems.route_path_system import route_to_dirname


class FileSystemAssetMaterializer(AssetMaterializer):
    def ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def copy_file(self, src: Path, dst: Path) -> None:
        if not dst.exists():
            shutil.copy2(src, dst)

    def copy_dir(self, src: Path, dst: Path) -> None:
        if not dst.exists():
            shutil.copytree(src, dst)


class PageAssetManager:
    """
    Manages the generation and cleanup logic of WebView page resource files.
    """

    def __init__(self, assets_root: Path, clean_on_start: bool = True):
        self.assets_root = assets_root
        self.clean_on_start = clean_on_start
        self._assets_cleaned = False
        self._generated_pages: set[str] = set()

    def _clean_assets_root(self):
        """
        Cleans the entire assets root directory, executed only once.
        """
        if self.clean_on_start and not self._assets_cleaned:
            path_utils.reset_dir(self.assets_root)
            self._assets_cleaned = True

    def _clean_page_dir(self, route: str) -> Path:
        """
        Cleans a single page directory and returns its Path.
        """
        page_dir = self.assets_root.joinpath(route_to_dirname(route))
        if page_dir.exists():
            path_utils.reset_dir(page_dir)
        return page_dir

    def prepare_page_dir(self, route: str) -> Path:
        """
        Prepares directory for page generation:
        1. Clean the entire assets root directory before first page generation (optional)
        2. Clean the current page directory
        3. Return the page directory Path
        """
        self._clean_assets_root()
        return self._clean_page_dir(route)

    def mark_page_generated(self, route: str):
        """
        Marks the page as generated to avoid duplicate cleanup.
        """
        self._generated_pages.add(route)

    def is_page_generated(self, route: str) -> bool:
        """
        Determines whether the page has been generated.
        """
        return route in self._generated_pages
