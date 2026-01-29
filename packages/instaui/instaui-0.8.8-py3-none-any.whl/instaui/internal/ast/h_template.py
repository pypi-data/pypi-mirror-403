from instaui.systems.dataclass_system import dataclass
from instaui.internal.ast.expression import ObjectExpr


@dataclass()
class HTemplateElementInfo:
    args: ObjectExpr
