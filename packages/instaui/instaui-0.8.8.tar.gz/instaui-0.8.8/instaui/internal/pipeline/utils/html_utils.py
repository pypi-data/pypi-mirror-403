from html import escape
from typing import Optional


def render_attrs(attrs: Optional[dict]) -> str:
    if not attrs:
        return ""

    parts: list[str] = []

    for k, v in attrs.items():
        if v is False or v is None:
            continue
        elif v is True:
            parts.append(k)
        else:
            parts.append(f'{k}="{escape(str(v), quote=True)}"')

    return " " + " ".join(parts)
