from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from instaui.systems import file_system

if TYPE_CHECKING:
    from instaui.internal.backend.fastapi.endpoints import ServerEndpoints


_THashPart = str
_HASH_PART_MAP: dict[_THashPart, Path] = {}
_PATH_URL_MAP: dict[Path, _THashPart] = {}


def get_folder_path(hash_part: str) -> Path:
    return _HASH_PART_MAP[hash_part]


def record_asset(path: Path, endpoints: ServerEndpoints):
    path = Path(path).resolve()
    is_file = path.is_file()

    folder_path = path.parent if is_file else path

    if folder_path not in _HASH_PART_MAP:
        hash_part = file_system.generate_hash_name_from_path(folder_path)
        _HASH_PART_MAP[hash_part] = folder_path
    else:
        hash_part = _PATH_URL_MAP[folder_path]

    folder_url = f"{endpoints.ASSETS_URL_WITH_PREFIX}/{hash_part}/"

    return f"{folder_url}{path.name}" if is_file else folder_url
