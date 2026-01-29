# from typing import Any, Optional
# from instaui.systems.dataclass_system import dataclass


# @dataclass(frozen=True)
# class ScriptTag:
#     content: str
#     script_attrs: Optional[dict[str, Any]] = None


from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


ScriptLoading = Literal["async", "defer", "blocking"]
ScriptPosition = Literal["head", "body"]


@dataclass(slots=True, frozen=True)
class JSAsset:
    kind: Literal["inline", "file", "url"]
    source: str | Path
    module: bool = False
    loading: ScriptLoading = "blocking"
    position: ScriptPosition = "body"
    attrs: dict[str, Any] = field(default_factory=dict)
