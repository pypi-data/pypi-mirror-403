from instaui.internal.ast.core import (
    Render,
    ComponentRef,
)
from instaui.internal.ast.expression import Expression


class ComponentRefCollector:
    def collect(self, expr: Expression, out: set[ComponentRef]) -> None:
        if isinstance(expr, ComponentRef):
            out.add(expr)

        elif isinstance(expr, Render):
            for v in expr.props.values():
                self.collect(v, out)

        else:
            for attr in vars(expr).values():
                if isinstance(attr, Expression):
                    self.collect(attr, out)
                elif isinstance(attr, (list, tuple)):
                    for x in attr:
                        if isinstance(x, Expression):
                            self.collect(x, out)
