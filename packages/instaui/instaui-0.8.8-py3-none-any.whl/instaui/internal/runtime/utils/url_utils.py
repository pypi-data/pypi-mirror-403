import base64
from pathlib import Path
from typing import Union
from urllib.parse import quote
from enum import StrEnum


class PREFIX(StrEnum):
    JS = "data:text/javascript;charset=utf-8"
    CSS = "data:text/css;charset=utf-8"
    ICON = "data:image/x-icon;base64"


def normalize_path_to_dataurl_or_cdn(path: Union[str, Path], prefix: PREFIX):
    if isinstance(path, Path):
        path = path.read_text(encoding="utf-8")
        return f"{prefix},{quote(path)}"

    return path


def normalize_path_to_base64_url(path: Path, prefix: PREFIX):
    return f"{prefix},{base64.b64encode(path.read_bytes()).decode('utf-8')}"
