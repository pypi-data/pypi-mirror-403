from __future__ import annotations
from typing import Any, Iterable, Optional, Union
from instaui.internal.ast.property_key import PropertyKey
from instaui.systems.dataclass_system import dataclass, field
from instaui.internal.ast.symbol import SymbolId


class Expression:
    pass


# Member access
@dataclass()
class MemberExpr(Expression):
    """
    a.x
    v.value
    """

    obj: Expression
    member: str


# Function call
@dataclass()
class CallExpr(Expression):
    """
    ref()
    ref(0)
    ref(0, 1)
    createApp(cp, {a:1})
    """

    callee: Expression
    args: tuple[Expression, ...] = field(default_factory=tuple)

    @classmethod
    def of(cls, callee: Expression, *args: Expression) -> CallExpr:
        return cls(callee=callee, args=args)


@dataclass()
class ObjectExpr(Expression):
    props: list[ObjectProperty]

    @classmethod
    def from_kwargs(cls, **kwargs: Optional[Expression]) -> ObjectExpr:
        return cls(
            props=[ObjectProperty(k, v) for k, v in kwargs.items() if v is not None]
        )

    @classmethod
    def from_dict(cls, kwargs: dict[Union[PropertyKey, str], Expression]) -> ObjectExpr:
        return cls(
            props=[ObjectProperty(k, v) for k, v in kwargs.items() if v is not None]
        )

    @classmethod
    def from_pairs(
        cls, pairs: Iterable[tuple[Union[PropertyKey, str], Expression | None]]
    ) -> ObjectExpr:
        return cls(props=[ObjectProperty(k, v) for k, v in pairs if v is not None])

    def __bool__(self) -> bool:
        return bool(self.props)


@dataclass()
class ListExpr(Expression):
    value: list[Expression]

    @classmethod
    def from_values(cls, *values: Expression) -> ListExpr:
        return cls(value=list(values))

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass()
class ObjectProperty:
    key: Union[PropertyKey, str]
    value: Optional[Expression] = None
    shorthand: bool = False


# Arrow function (for setup / render)
@dataclass()
class ArrowFunctionExpr(Expression):
    body: Optional[Expression] = None
    params: Optional[Expression] = None


@dataclass()
class RawFunctionExpr(Expression):
    """
    Directly embed a string of JavaScript anonymous function.
    For example:
        "function(x) { return x + 1; }"
        "() => ({ count: 0 })"
    Note: The caller must ensure the string is a valid JS function expression.
    """

    js_code: str


@dataclass()
class IdentifierRef(Expression):
    id: SymbolId


# Literal
@dataclass()
class Literal(Expression):
    value: Any


@dataclass()
class StringLiteral(Expression):
    value: Any


@dataclass(frozen=True)
class NullExpr(Expression):
    pass


@dataclass(frozen=True)
class UndefinedExpr(Expression):
    pass


NULL = NullExpr()
UNDEFINED = UndefinedExpr()


@dataclass()
class ObjectLiteral(Expression):
    props: dict[str, Any]

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> ObjectLiteral:
        return cls(props={k: v for k, v in kwargs.items() if v is not None})

    def __bool__(self) -> bool:
        return bool(self.props)


@dataclass()
class ListLiteral(Expression):
    value: list

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass(frozen=True)
class JsonLiteralExpr(Expression):
    value: Any

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass()
class PathTrackerBindableCall(Expression):
    target: Expression
    args: Expression


@dataclass()
class StrFormatCall(Expression):
    args: Expression


@dataclass()
class BackendValueRefExpr(Expression):
    ref_id: int


@dataclass()
class ToValueCall(Expression):
    value: Expression
