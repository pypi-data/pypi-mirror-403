from typing import Iterable
from instaui.internal.ast.core import App, Element
from instaui.internal.ast.expression import CallExpr, Literal, IdentifierRef, ObjectExpr
from instaui.internal.ast.sfc_template import (
    TemplateDirectiveInfo,
    TemplateElementInfo,
    TemplateTagKind,
)
from instaui.internal.pipeline.normalize.base import AstPass

SUPPORTED_VUE_DIRECTIVES: dict[str, int] = {
    "if": 1,
    "for": 2,
    "show": 1,
}


class NormalizeForVueSfcTemplate(AstPass):
    def run(self, ast: App):
        """
        In-place normalize.
        If no exception is raised, ast is guaranteed to be Vue-template-safe.
        """
        for el in self.walk_elements(ast):
            self.normalize_element_for_vue(el)

        return ast

    def walk_elements(self, ast: App) -> Iterable[Element]:
        for comp in ast.components:
            for render in comp.renders:
                if isinstance(render, Element):
                    yield render

    def normalize_element_for_vue(self, el: Element) -> None:
        tag_kind = self.normalize_tag_for_vue(el)

        props_ok = self.normalize_props_for_vue(el)
        events_ok = self.normalize_events_for_vue(el)
        directive_infos = self.normalize_directives_for_vue(el)

        el._tpl = TemplateElementInfo(
            tag_kind=tag_kind,
            props_is_object_literal=props_ok,
            events_is_object_literal=events_ok,
            directives=directive_infos,
        )

    def normalize_tag_for_vue(self, el: Element) -> TemplateTagKind:
        tag = el.tag

        if isinstance(tag, Literal):
            return TemplateTagKind.HTML

        if isinstance(tag, IdentifierRef):
            return TemplateTagKind.COMPONENT

        # <component :is="expr">
        return TemplateTagKind.DYNAMIC

    def normalize_props_for_vue(self, el: Element) -> bool:
        if el.props is None:
            return False

        if not isinstance(el.props, ObjectExpr):
            raise TemplateNormalizeError(
                "In Vue SFC template mode, element props must be an object literal"
            )

        return True

    def normalize_events_for_vue(self, el: Element) -> bool:
        if el.events is None:
            return False

        if not isinstance(el.events, ObjectExpr):
            raise TemplateNormalizeError(
                "In Vue SFC template mode, events must be an object literal"
            )

        return True

    def normalize_directives_for_vue(self, el: Element) -> list[TemplateDirectiveInfo]:
        infos: list[TemplateDirectiveInfo] = []

        if not el.dirs:
            return infos

        for call in el.dirs:
            if not isinstance(call, CallExpr):
                raise TemplateNormalizeError("Directive must be a call expression")

            if not isinstance(call.callee, IdentifierRef):
                raise TemplateNormalizeError("Directive callee must be an identifier")

            name = call.callee.name
            if name not in SUPPORTED_VUE_DIRECTIVES:
                raise TemplateNormalizeError(f"Unsupported Vue directive: {name}")

            expected_args = SUPPORTED_VUE_DIRECTIVES[name]
            actual_args = len(call.args or [])

            if actual_args != expected_args:
                raise TemplateNormalizeError(
                    f"Directive '{name}' expects {expected_args} arguments, "
                    f"got {actual_args}"
                )

            infos.append(
                TemplateDirectiveInfo(
                    name=name,
                    arg_count=expected_args,
                )
            )

        return infos


class TemplateNormalizeError(Exception):
    pass
