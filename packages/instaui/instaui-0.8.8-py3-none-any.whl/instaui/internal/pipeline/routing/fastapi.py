import re
from .base import RouteSyntaxAdapter


_FASTAPI_PARAM_RE = re.compile(
    r"{\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*(?::[a-zA-Z_]+)?\s*}"
)


class FastAPIRouteSyntaxAdapter(RouteSyntaxAdapter):
    """
    Normalize FastAPI-style route syntax into frontend-friendly form.

    Examples:
        "/users/{id}"        -> "/users/:id"
        "/users/{id:int}"    -> "/users/:id"
        "/files/{path:path}" -> "/files/:path"
    """

    def normalize(self, path: str) -> str:
        return _FASTAPI_PARAM_RE.sub(
            lambda m: f":{m.group('name')}",
            path,
        )
