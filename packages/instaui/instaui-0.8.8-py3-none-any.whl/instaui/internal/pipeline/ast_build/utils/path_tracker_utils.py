from typing import cast
from instaui.internal.ui.path_var import PathInfo


def normalize_paths(path_infos: list[PathInfo]):
    all_binds = all(path.is_bind for path in path_infos)

    if all_binds:
        return [cast(list, path.args)[0] for path in path_infos]

    return [normalize_path_info(path) for path in path_infos]


def normalize_path_info(path_info: PathInfo):
    if path_info.args is None:
        return [path_info.name]

    return [
        path_info.name,
        path_info.args,
    ]
