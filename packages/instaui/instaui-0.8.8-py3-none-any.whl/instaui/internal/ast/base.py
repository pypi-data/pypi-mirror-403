from instaui.debug.model import SourceSpan
from instaui.systems.dataclass_system import dataclass


@dataclass
class AstNode:
    source: SourceSpan
