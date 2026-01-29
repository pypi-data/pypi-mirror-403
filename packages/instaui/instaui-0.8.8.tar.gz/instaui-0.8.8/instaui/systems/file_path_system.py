from pathlib import Path
from typing import Union
import inspect


def get_caller_path(up: int = 2) -> Path:
    """
    Get the file path of the caller at the specified call stack level.

    Args:
        up: The number of call stack levels to go up. Default is 1 (direct caller).

    Returns:
        Path: The resolved file path of the caller.

    Raises:
        RuntimeError: If the call stack is too shallow.
    """
    return _get_caller_file(up)


def resolve_relative_path(path_or_str: Union[str, Path], up: int = 1) -> Path:
    if isinstance(path_or_str, Path):
        return path_or_str.resolve()

    caller_file = _get_caller_file(up + 1)
    return (caller_file.parent / path_or_str).resolve()


def _get_caller_file(up: int) -> Path:
    """
    Return the resolved Path of the caller file `up` levels above.
    """
    frame = inspect.currentframe()
    try:
        # +1 to skip this helper itself
        for _ in range(up + 1):
            if frame is None:
                raise RuntimeError("Frame stack too shallow")
            frame = frame.f_back

        if frame is None:
            raise RuntimeError("Frame stack too shallow")

        return Path(inspect.getfile(frame)).resolve()
    finally:
        del frame
