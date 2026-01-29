_DEV_MODE = False
_FROZEN = False


def set_dev(value: bool) -> None:
    global _DEV_MODE, _FROZEN
    if _FROZEN:
        raise RuntimeError(
            "instaui dev mode is already frozen; "
            "import instaui.dev must be called before importing ui"
        )
    _DEV_MODE = bool(value)


def is_dev() -> bool:
    return _DEV_MODE


def freeze() -> None:
    """
    Called by subsystems that rely on dev/prod mode
    to prevent late mutation.
    """
    global _FROZEN
    _FROZEN = True
