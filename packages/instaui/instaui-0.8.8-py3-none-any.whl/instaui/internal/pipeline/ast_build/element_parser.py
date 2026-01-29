from __future__ import annotations
from typing import Optional
from instaui.internal.ast.property_key import StringKey
from instaui.internal.pipeline.ast_build.base import (
    RenderBuilderProtocol,
)
from instaui.internal.pipeline.ast_build.expr_builder import ExprBuilder

from instaui.internal.ui.event_args import EventArgs
from instaui.internal.ui.slot import Slot
from instaui.systems.dict_flow_system import (
    process_dict,
    remove_empty_collection,
    remove_none,
    repr_dict_keys,
)
from instaui.internal.ui.element import Element
from instaui.internal.ast import core as ast_core
from instaui.internal.ast import expression
from instaui.internal.pipeline.ast_build.context import AstBuilderContext


class ElementParser:
    def __init__(
        self, ctx: AstBuilderContext, render_builder: RenderBuilderProtocol
    ) -> None:
        self.ctx = ctx
        self._expr_builder = ExprBuilder(ctx)
        self._render_builder = render_builder

    def parse(self, element: Element) -> ast_core.Element:
        tag = self._expr_builder.build(element.tag)

        props = (
            process_dict(
                {
                    "bProps": element._binding_props,
                    "pProps": element._proxy_props,
                    "sProps": element._props,
                    "ref": element._element_ref,
                },
                [remove_none, remove_empty_collection, repr_dict_keys],
            )
            or None
        )

        props = self._create_props(element) if props else None
        events = self._create_events(element)
        dirs = self._create_directives(element)
        classes = self._create_classes(element)
        styles = self._create_styles(element)
        lifecycles = self._create_lifecycles(element)
        slots = self._create_slots(element)

        return ast_core.Element(
            tag=tag,
            props=props,
            events=events,
            dirs=dirs,
            classes=classes,
            styles=styles,
            lifecycles=lifecycles,
            slots=slots,
        )

    def _create_slots(self, element: Element) -> Optional[dict[str, ast_core.Slot]]:
        if not element._slots:
            return None

        return {
            name: self._parse_slot(name, slot) for name, slot in element._slots.items()
        }

    def _parse_slot(self, name: str, slot: Slot) -> ast_core.Slot:
        prop = None
        if slot._slot_prop._used:
            prop = self.ctx.var_mapper.get_or_create_id(slot._slot_prop)
            self.ctx.component_scope_manager.declare_var(prop)

        return ast_core.Slot(
            name=expression.StringLiteral(name),
            used_prop=prop,
            body=[self._render_builder.build(child) for child in slot.children],
        )

    def _create_lifecycles(
        self, element: Element
    ) -> Optional[dict[str, expression.Expression]]:
        if not element._lifecycle_events:
            return None

        return {
            event_name: expression.ListExpr(
                [self._event_call(event_arg) for event_arg in event_args]
            )
            for event_name, event_args in element._lifecycle_events.items()
        }

    def _create_styles(self, element: Element) -> Optional[ast_core.ElementStyles]:
        styles = ast_core.ElementStyles()
        if element._style:
            styles.static = expression.JsonLiteralExpr(element._style)

        if element._binging_style:
            styles.binding = expression.ObjectExpr.from_pairs(
                (StringKey(name), self._expr_builder.build(expr))
                for name, expr in element._binging_style.items()
            )

        if element._proxy_style:
            styles.proxy = [
                self._expr_builder.build(expr) for expr in element._proxy_style
            ]

        return styles or None

    def _create_classes(self, element: Element) -> Optional[ast_core.ElementClasses]:
        classes = ast_core.ElementClasses()
        if element._str_classes:
            classes.static = expression.ListLiteral(element._str_classes)

        if element._map_classes:
            classes.maps = expression.ObjectExpr.from_pairs(
                (StringKey(name), self._expr_builder.build(expr))
                for name, expr in element._map_classes.items()
            )

        if element._binding_classes:
            classes.binding = [
                self._expr_builder.build(expr) for expr in element._binding_classes
            ]

        return classes or None

    def _create_props(self, element: Element):
        props = ast_core.ElementProp()
        if element._binding_props:
            props.binding = {
                name: self._expr_builder.build(expr)
                for name, expr in element._binding_props.items()
            }
        if element._proxy_props:
            props.proxy = [
                self._expr_builder.build(expr) for expr in element._proxy_props
            ]

        if element._props:
            props.static = expression.JsonLiteralExpr(element._props)

        if element._element_ref:
            props.ref = self._expr_builder.build_Variable(element._element_ref)

        return props or None

    def _create_directives(
        self, element: Element
    ) -> Optional[list[ast_core.Directive]]:
        if not element._directives:
            return None

        return [
            ast_core.Directive(
                name=expression.Literal(directive.name),
                value=self._expr_builder.build(directive._value),
                arg=expression.Literal(directive._arg) if directive._arg else None,
                sys=expression.Literal(int(directive._is_sys))
                if directive._is_sys
                else None,
                mf=expression.ListLiteral(directive._modifiers)
                if directive._modifiers
                else None,
            )
            for directive in element._directives.keys()
        ]

    def _create_events(self, element: Element) -> Optional[expression.ObjectExpr]:
        if not element._events:
            return None

        return expression.ObjectExpr.from_pairs(
            (
                StringKey(event_name),
                expression.ListExpr(
                    [self._event_call(event_arg) for event_arg in event_args]
                ),
            )
            for event_name, event_args in element._events.items()
        )

    def _event_call(self, event_arg: EventArgs) -> expression.CallExpr:
        # _$v3.fn({params: [], modifier: []})

        target = expression.IdentifierRef(
            self.ctx.var_mapper.get_or_create_id(event_arg.event)
        )

        args = {}
        if event_arg.params:
            args["params"] = self._expr_builder.list_expr(values=event_arg.params)
        if event_arg.modifier:
            args["modifier"] = expression.ListLiteral(event_arg.modifier)

        return expression.CallExpr.of(
            expression.MemberExpr(obj=target, member="fn"),
            expression.ObjectExpr.from_kwargs(**args),
        )
