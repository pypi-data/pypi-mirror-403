from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, Optional, TypeVar
from instaui.protocol.invocation.spec import InvocationSpec

if TYPE_CHECKING:
    from instaui.internal.runtime.render_ctx import RenderContext


SpecT = TypeVar("SpecT", bound=InvocationSpec)


class BackendInvocationKind(Enum):
    COMPUTED = auto()
    WATCH = auto()
    EVENT = auto()
    FILE_UPLOAD = auto()


@dataclass(frozen=True)
class BackendInvocation(Generic[SpecT]):
    kind: BackendInvocationKind
    fn: Callable
    render_ctx: RenderContext
    spec: Optional[SpecT] = None
    source: Optional[str] = None  # debug info
