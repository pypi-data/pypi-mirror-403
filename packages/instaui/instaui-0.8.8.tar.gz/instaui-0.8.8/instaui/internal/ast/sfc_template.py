from dataclasses import dataclass, field
from enum import Enum
from typing import List


class TemplateTagKind(Enum):
    HTML = "html"
    COMPONENT = "component"
    DYNAMIC = "dynamic"


@dataclass(frozen=True)
class TemplateDirectiveInfo:
    """
    Confirmed during normalize phase:
    - This is a Vue template supported directive
    - Its CallExpr structure is valid
    """

    name: str  # if / for / show
    arg_count: int


@dataclass
class TemplateElementInfo:
    """
    Vue SFC template codegen specific, strongly typed annotation
    """

    # tag related
    tag_kind: TemplateTagKind

    # Whether props / events have been validated as template-safe
    props_is_object_literal: bool = False
    events_is_object_literal: bool = False

    # Directive information (one-to-one correspondence with el.dirs)
    directives: List[TemplateDirectiveInfo] = field(default_factory=list)
