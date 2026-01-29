from typing import TYPE_CHECKING
from .version import __version__

from .zero import ZeroLauncher as zero


if TYPE_CHECKING:
    # only for IDE
    from . import facade_ui as ui
    from instaui.internal.ui import html, file_io
else:

    def __getattr__(name: str):
        match name:
            case "ui":
                from . import facade_ui as ui

                return ui
            case "html":
                from instaui.internal.ui import html

                return html
            case "file_io":
                from instaui.internal.ui import file_io

                return file_io
            case _:
                raise AttributeError(name)


__all__ = [
    "__version__",
    "ui",
    "html",
    "file_io",
    "zero",
]
