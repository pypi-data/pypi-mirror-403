from __future__ import annotations
from typing import Optional
from instaui.internal.ast.base import AstNode
from instaui.internal.ast.expression import (
    Expression,
    IdentifierRef,
    JsonLiteralExpr,
    ListLiteral,
    ObjectExpr,
    ObjectLiteral,
    RawFunctionExpr,
    Literal,
    StringLiteral,
)
from instaui.internal.ast.symbol import SymbolId
from instaui.internal.ast.sfc_template import TemplateElementInfo
from instaui.systems.dataclass_system import dataclass, field


@dataclass()
class App:
    root: ComponentRef
    components: list[ComponentDef]
    bootstrap: AppBootstrap


@dataclass()
class SvgSprite:
    args: ObjectLiteral


@dataclass()
class AppBootstrap:
    target: SymbolId
    root: ComponentRef
    meta: Expression
    plugins: Optional[list[Plugin]] = None
    custom_components: Optional[list[CustomComponent]] = None


@dataclass()
class Plugin:
    url: StringLiteral
    options: Optional[ObjectExpr | JsonLiteralExpr]


@dataclass()
class CustomComponent:
    name: StringLiteral
    url: StringLiteral


@dataclass()
class ComponentRef:
    id: SymbolId
    vfor: Optional[ComponentRefVFor] = None


@dataclass()
class ComponentRefVFor:
    index: list[SymbolId] = field(default_factory=list)
    value: list[SymbolId] = field(default_factory=list)
    item_key: list[SymbolId] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.index or self.value or self.item_key)


@dataclass()
class Render:
    pass


@dataclass()
class ComponentRefRender(Render):
    ref: ComponentRef


@dataclass()
class Element(Render):
    tag: Expression
    props: Optional[ElementProp] = None
    classes: Optional[ElementClasses] = None
    styles: Optional[ElementStyles] = None
    events: Optional[ObjectExpr] = None
    dirs: Optional[list[Directive]] = None
    lifecycles: Optional[dict[str, Expression]] = None
    slots: Optional[dict[str, Slot]] = None

    # normalize_for_template
    _tpl: Optional[TemplateElementInfo] = None


@dataclass()
class VFor(Render):
    fkey: Literal
    array: VForArray
    used_item: Optional[SymbolId] = None
    used_index: Optional[SymbolId] = None
    used_key: Optional[SymbolId] = None
    transition_group: Optional[ObjectLiteral] = None
    children: Optional[list[Render]] = None


@dataclass()
class MatchRender(Render):
    condition: Expression
    cases: list[MatchCase]
    default_case: Optional[list[Render]] = None


@dataclass()
class MatchCase:
    value: Expression
    children: list[Render]


@dataclass()
class ContentRender:
    content: Expression


@dataclass()
class VIf(Render):
    condition: Expression
    children: Optional[list[Render]] = None


@dataclass()
class VForArray:
    type: Literal
    value: Expression


@dataclass()
class Slot:
    """
    One slot = one render fragment.
    It will ultimately be codegen'ed into () => [...].
    """

    name: StringLiteral  # "default" / "header" / ...
    body: list[Render]
    used_prop: Optional[SymbolId] = None


@dataclass()
class ElementProp:
    binding: Optional[dict[str, Expression]] = None
    proxy: Optional[list[Expression]] = None
    static: Optional[JsonLiteralExpr] = None
    ref: Optional[IdentifierRef] = None

    def __bool__(self):
        return bool(self.binding or self.proxy or self.static or self.ref)


@dataclass()
class ElementClasses:
    binding: Optional[list[Expression]] = None
    static: Optional[ListLiteral] = None
    maps: Optional[ObjectExpr] = None

    def __bool__(self):
        return bool(self.binding or self.static or self.maps)


@dataclass()
class ElementStyles:
    static: Optional[JsonLiteralExpr] = None
    binding: Optional[ObjectExpr] = None
    proxy: Optional[list[Expression]] = None

    def __bool__(self):
        return bool(self.binding or self.static or self.proxy)


@dataclass()
class Directive:
    name: Literal
    value: Expression
    sys: Optional[Literal] = None
    arg: Optional[Literal] = None
    mf: Optional[ListLiteral] = None


@dataclass()
class ComponentDef:
    id: SymbolId

    variables: list[VariableDecl] = field(default_factory=list)
    renders: list[Render] = field(default_factory=list)
    web_watch_tasks: Optional[list[WebWatchTask]] = None
    js_watchs: Optional[list[JsWatchCall]] = None
    expr_watchs: Optional[list[ExprWatchCall]] = None
    on_mounted_calls: list[RawFunctionExpr] = field(default_factory=list)
    injects: Optional[list[SymbolId]] = None
    provides: Optional[list[SymbolId]] = None

    vars: list[SymbolId] = field(default_factory=list)


@dataclass()
class WebWatchTask(AstNode):
    fn: BackendFunctionRef
    args: ObjectExpr


@dataclass()
class JsWatchCall:
    args: ObjectExpr


@dataclass()
class ExprWatchCall:
    args: ObjectExpr


@dataclass()
class VariableDecl(AstNode):
    target: SymbolId


@dataclass()
class ConstDataDecl(VariableDecl):
    value: Expression


@dataclass()
class ElementRefDecl(VariableDecl):
    pass


@dataclass()
class ExprComputedDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class ExprEventDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class RefDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class JsComputedDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class JsEventDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class JsFnDecl(VariableDecl):
    fn: RawFunctionExpr


@dataclass()
class CustomRefDecl(VariableDecl):
    module: str
    name: str
    params: Optional[list[Expression]] = None


@dataclass()
class BackendComputedDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class BackendEventDecl(VariableDecl):
    args: ObjectExpr


@dataclass()
class BackendFunctionRef:
    ref_id: int
