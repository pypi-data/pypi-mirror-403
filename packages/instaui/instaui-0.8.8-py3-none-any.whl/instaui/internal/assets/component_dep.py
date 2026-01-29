from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Optional, Sequence
from instaui.constants.runtime import RuntimeMode
from instaui.systems.dataclass_system import dataclass, field


if TYPE_CHECKING:
    from instaui.internal.assets.css_assets import CssAsset
    from instaui.internal.ui.element import Element


@dataclass(frozen=True)
class ComponentDependencyOverride:
    zero_externals: Mapping[str, Path] | None = None
    zero_css: Sequence[str | Path | CssAsset] | None = None


@dataclass(frozen=True)
class ComponentDependencyInfo:
    tag_name: str = field(hash=True)
    esm: Path = field(hash=False)
    externals: dict[str, Path] = field(default_factory=dict, compare=False, hash=False)
    css: list[str | Path | CssAsset] = field(
        default_factory=list, compare=False, hash=False
    )
    overrides: Optional[Mapping[RuntimeMode, ComponentDependencyOverride]] = field(
        default=None, compare=False, hash=False
    )


@dataclass(frozen=True)
class ComponentDependencyRecord:
    component: type[Element]
    dependency: ComponentDependencyInfo


class ComponentDependencyRegistry:
    def __init__(self):
        self._records: set[ComponentDependencyRecord] = set()

    def add(self, component: type[Element], dep: ComponentDependencyInfo):
        self._records.add(ComponentDependencyRecord(component, dep))

    @property
    def records(self) -> set[ComponentDependencyRecord]:
        return self._records
