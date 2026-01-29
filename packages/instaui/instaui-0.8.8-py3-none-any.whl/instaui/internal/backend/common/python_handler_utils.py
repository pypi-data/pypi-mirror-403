from typing import Callable, Hashable, Optional, Sequence
from instaui.systems import func_system


def create_handler_key(
    page_path: str,
    handler: Callable,
    debug_mode: bool,
    extra_key: Optional[Sequence[Hashable]] = None,
):
    _, lineno, _ = func_system.get_function_location_info(handler)
    key = f"path:{page_path}|line:{lineno}" if debug_mode else f"{page_path}|{lineno}"
    if extra_key:
        key = repr(tuple(extra_key) + (key,))

    return key
