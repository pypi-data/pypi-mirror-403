import base64
from pathlib import Path
from urllib.parse import quote
from enum import Enum
import mimetypes
from .resolver import AssetResolver


class PREFIX(str, Enum):
    JS = "data:text/javascript;charset=utf-8"
    CSS = "data:text/css;charset=utf-8"
    ICON = "data:image/x-icon;base64"


PREFIX_MAP = {
    "js": PREFIX.JS.value,
    "mjs": PREFIX.JS.value,
    "css": PREFIX.CSS.value,
    "ico": PREFIX.ICON.value,
}


class ZeroAssetResolver(AssetResolver):
    def resolve_asset(self, path: Path) -> str:
        return _normalize_path_to_dataurl(path)


def _normalize_path_to_dataurl(path: Path):
    prefix, ext = _get_prefix(path)

    if ext == "ico":
        return _normalize_path_to_base64_url(path, prefix)

    content = path.read_text(encoding="utf-8")
    return f"{prefix},{quote(content)}"


def _normalize_path_to_base64_url(path: Path, prefix: str):
    return f"{prefix},{base64.b64encode(path.read_bytes()).decode('utf-8')}"


def _get_prefix(path: Path):
    ext = path.suffix.lstrip(".")
    prefix = PREFIX_MAP.get(ext, None)
    if not prefix:
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            raise RuntimeError(f"Unknown mime type: {path}")

        prefix = f"data:{mime};base64"

    return prefix, ext
