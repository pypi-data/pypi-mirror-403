from typing import Optional, Union, cast
from instaui.constants.ui import DEFAULT_SLOT_NAME
from instaui.internal import import_presets
from instaui.internal.ast import value_rewriter
from instaui.internal.ast.core import (
    Directive,
    Element,
    ElementClasses,
    ElementProp,
    ElementStyles,
    Slot,
)
from instaui.internal.ast import expression
from instaui.internal.ast.property_key import StringKey
from instaui.internal.codegen.base import RenderEmitter
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class ElementRenderer:
    def __init__(self, ctx: FileCodegenContext, render_emitter: RenderEmitter) -> None:
        self.ctx = ctx
        self.expr = ExpressionCodegen(ctx)
        self.render_emitter = render_emitter

    def emit(self, element: Element) -> str:
        method = self.ctx.imports.use_from_preset(
            import_presets.Instaui.render_component()
        )

        obj = expression.ObjectExpr.from_kwargs(
            tag=element.tag,
            props=self.normalize_props(element.props),
            classes=self.normalize_classes(element.classes),
            style=self.normalize_styles(element.styles),
            events=self.normalize_events(element.events),
            dirs=self.normalize_directives(element.dirs),
            lifeEvents=self.normalize_life_events(element.lifecycles),
            slots=self.emit_slots(element),
        )

        return f"{method}({self.expr.emit(obj)})"

    def emit_slots(
        self, element: Element
    ) -> Union[expression.ObjectExpr, expression.ArrowFunctionExpr, None]:
        if not element.slots:
            return None

        slots: dict[str, expression.Expression] = {}

        for slot in element.slots.values():
            slots[self.expr.emit(slot.name)] = self.emit_slot_body(slot)

        if len(slots) == 1 and DEFAULT_SLOT_NAME in slots:
            return cast(expression.ArrowFunctionExpr, slots[DEFAULT_SLOT_NAME])

        return expression.ObjectExpr.from_kwargs(**slots)

    def emit_slot_body(self, slot: Slot) -> expression.Expression:
        exprs = [
            expression.RawFunctionExpr(self.render_emitter.emit_render(n))
            for n in slot.body
        ]

        params = expression.IdentifierRef(slot.used_prop) if slot.used_prop else None

        return expression.ArrowFunctionExpr(
            body=expression.ListExpr.from_values(*exprs), params=params
        )

    def normalize_props(
        self, props: Optional[ElementProp]
    ) -> Optional[expression.ObjectExpr]:
        if not props:
            return None

        return expression.ObjectExpr.from_kwargs(
            bProps=expression.ObjectExpr.from_dict(
                value_rewriter.rewrite_string_key_shallow(props.binding)
            )
            if props.binding
            else None,
            pProps=expression.ListExpr.from_values(*props.proxy)
            if props.proxy
            else None,
            sProps=props.static,
            ref=props.ref,
        )

    def normalize_life_events(
        self, lifecycles: Optional[dict[str, expression.Expression]]
    ) -> Optional[expression.ObjectExpr]:
        if not lifecycles:
            return None

        return expression.ObjectExpr.from_dict(
            {event_name: event_args for event_name, event_args in lifecycles.items()}
        )

    def normalize_styles(
        self, styles: Optional[ElementStyles]
    ) -> Optional[expression.ObjectExpr]:
        if not styles:
            return None

        return expression.ObjectExpr.from_kwargs(
            sStyle=styles.static if styles.static else None,
            bStyle=styles.binding if styles.binding else None,
            pStyle=expression.ListExpr.from_values(*styles.proxy)
            if styles.proxy
            else None,
        )

    def normalize_classes(
        self, classes: Optional[ElementClasses]
    ) -> Optional[expression.Expression]:
        if not classes:
            return None
        if classes.static and not classes.binding and not classes.maps:
            return expression.Literal(" ".join(classes.static.value))

        return expression.ObjectExpr.from_kwargs(
            sClass=classes.static if classes.static else None,
            bClass=expression.ListExpr.from_values(*classes.binding)
            if classes.binding
            else None,
            mClass=classes.maps if classes.maps else None,
        )

    def normalize_directives(self, dirs: Optional[list[Directive]]):
        if not dirs:
            return None

        return expression.ListExpr.from_values(
            *[
                expression.ObjectExpr.from_kwargs(
                    name=dir.name,
                    value=dir.value,
                    sys=dir.sys,
                    arg=dir.arg,
                    mf=dir.mf,
                )
                for dir in dirs
            ]
        )

    def normalize_events(
        self, arg: Optional[expression.ObjectExpr]
    ) -> Optional[expression.ObjectExpr]:
        if not arg:
            return None
        return expression.ObjectExpr.from_pairs(
            (_normalize_event_name(prop), prop.value) for prop in arg.props
        )


def _normalize_event_name(prop: expression.ObjectProperty) -> StringKey:
    """'click' -> 'onClick' , 'press-enter' -> 'onPressEnter' , 'pressEnter' -> 'onPressEnter'"""

    event_name = cast(StringKey, prop.key).value

    if event_name.startswith("on-"):
        event_name = event_name[3:]

    if event_name.startswith("on"):
        event_name = event_name[2:]

    parts = event_name.split("-")
    formatted_parts = [part[0].upper() + part[1:] for part in parts]

    return StringKey("".join(["on", *formatted_parts]))
