import html
from typing import Any, Optional


def dict_to_html_attrs(attrs: Optional[dict[str, Any]]) -> str:
    """
    Convert a dict to an HTML attributes string.

    Example:
        {"id": "app", "class": "container", "disabled": True}
        -> 'id="app" class="container" disabled'
    """
    if not attrs:
        return ""
    parts: list[str] = []

    for key, value in attrs.items():
        if value is None:
            continue

        if value is True:
            parts.append(key)
            continue

        if value is False:
            continue

        escaped_value = html.escape(str(value), quote=True)
        parts.append(f'{key}="{escaped_value}"')

    return " ".join(parts)
