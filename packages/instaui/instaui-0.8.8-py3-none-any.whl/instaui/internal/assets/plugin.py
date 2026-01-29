from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol, Union
from instaui.systems.dataclass_system import dataclass, field

if TYPE_CHECKING:
    from instaui.internal.ui._scope import Scope
    from instaui.internal.assets.css_assets import CssAsset


class ParseScopeFn(Protocol):
    def __call__(self, scope: Scope) -> Any: ...


class StringKeyFn(Protocol):
    def __call__(self, key: str) -> Any: ...


class PluginOptionsBuilder(Protocol):
    def __call__(self, parse_key: StringKeyFn, parse_scope: ParseScopeFn) -> dict: ...


@dataclass(frozen=True)
class PluginDependencyInfo:
    name: str = field(hash=True)
    esm: Path = field(hash=False)
    externals: dict[str, Path] = field(default_factory=dict, compare=False, hash=False)
    css: list[Union[str, Path, CssAsset]] = field(
        default_factory=list, compare=False, hash=False
    )
    options: Optional[dict | PluginOptionsBuilder] = field(hash=False, default=None)
