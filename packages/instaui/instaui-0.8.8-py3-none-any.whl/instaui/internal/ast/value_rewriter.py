from typing import Any
from instaui.internal.ast import property_key


def rewrite_string_key_shallow(value: dict) -> Any:
    return {property_key.StringKey(k): v for k, v in value.items()}
