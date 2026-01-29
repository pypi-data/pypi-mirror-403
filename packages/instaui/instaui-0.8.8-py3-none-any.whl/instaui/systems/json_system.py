from typing import Any
import orjson as json


def to_json_str(value: Any):
    return json.dumps(value).decode("utf-8")
