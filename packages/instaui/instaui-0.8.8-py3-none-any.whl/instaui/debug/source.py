import sys
from instaui.debug.model import SourceSpan
from instaui.debug.source_fallback import _get_source_span_by_module_filter
from .config import is_dev, freeze


# -------------------------
# prod implementation
# -------------------------
class NullSourceSpan:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<NoSourceSpan>"


_NULL_SOURCE_SPAN = NullSourceSpan()


def _get_source_span_prod() -> SourceSpan:
    return _NULL_SOURCE_SPAN  # type: ignore


# -------------------------
# dev implementation
# -------------------------
def _get_source_span_dev():
    import inspect

    frame = inspect.currentframe()
    f = frame.f_back if frame else None

    while f:
        fn = f.f_globals.get(f.f_code.co_name)
        if getattr(fn, "__instaui_user_api__", False):
            f = f.f_back
            assert f is not None

            column = None
            if sys.version_info >= (3, 11):
                column = _get_frame_column(f)

            return SourceSpan(
                file=f.f_code.co_filename,
                line=f.f_lineno,
                function=f.f_code.co_name,
                column=column,
            )
        f = f.f_back

    # fallback
    return _get_source_span_by_module_filter()


def _get_frame_column(frame) -> int | None:
    # Python 3.11+ only
    try:
        code = frame.f_code
        positions = code.co_positions()
        index = frame.f_lasti // 2

        pos = list(positions)[index]
        _, _, col_start, _ = pos
        return col_start
    except Exception:
        return None


# -------------------------
# import-time binding
# -------------------------
if is_dev():
    get_source_span = _get_source_span_dev
else:
    get_source_span = _get_source_span_prod


freeze()
