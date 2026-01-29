import inspect
from instaui.debug.model import SourceSpan

_INTERNAL_MODULE_PREFIXES = ("instaui.",)


_INTERNAL_PATH_KEYWORDS = (
    "/instaui/",
    "\\instaui\\",
)


def _is_internal_frame(frame) -> bool:
    module = frame.f_globals.get("__name__", "")
    if any(module.startswith(p) for p in _INTERNAL_MODULE_PREFIXES):
        return True

    filename = frame.f_code.co_filename
    if any(k in filename for k in _INTERNAL_PATH_KEYWORDS):
        return True

    return False


def _get_source_span_by_module_filter() -> SourceSpan:
    frame = inspect.currentframe()
    if frame is None:
        return _unknown_source()

    f = frame.f_back

    while f is not None:
        if not _is_internal_frame(f):
            return SourceSpan(
                file=f.f_code.co_filename,
                line=f.f_lineno,
                function=f.f_code.co_name,
            )
        f = f.f_back

    return _unknown_source()


def _unknown_source() -> SourceSpan:
    return SourceSpan(
        file="<unknown>",
        line=0,
        function="<unknown>",
    )
