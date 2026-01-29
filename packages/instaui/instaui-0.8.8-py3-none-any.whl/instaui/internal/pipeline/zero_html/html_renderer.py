from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional, Union
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader
from instaui.internal.codegen.program_codegen import CodegenResult
from .html_context import HtmlRenderContext


class ZeroHtmlRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, codegen: CodegenResult, options: HtmlOptions) -> str:
        template = self.env.get_template("zero.html.j2")

        ctx = HtmlRenderContext(
            app_var=codegen.app_var,
            title=options.title,
            favicon_url=options.favicon_url,
            css_links=options.css_links,
            style_tags=options.style_tags,
            script_tags_in_head=options.script_tags_in_head,
            script_tags_in_body=options.script_tags_in_body,
            entry_code=codegen.entry_code,
            import_map=options.import_map,
            icons_svg_fragment=self._create_icons_svg_content(options.icons_svg_path)
            if options.icons_svg_path
            else None,
        )

        return template.render(model=ctx)

    def _create_icons_svg_content(
        self,
        icons_svg_path: Union[Path, Callable[[], Path]],
    ) -> Optional[str]:
        if callable(icons_svg_path):
            icons_svg_path = icons_svg_path()
            return (
                icons_svg_path
                if isinstance(icons_svg_path, str)
                else icons_svg_path.read_text(encoding="utf-8")
            )

        return icons_svg_path.read_text(encoding="utf-8")


@dataclass()
class HtmlOptions:
    favicon_url: str
    title: str = "instaui"

    css_links: list[str] = field(default_factory=list)
    style_tags: list[tuple[Optional[str], str]] = field(default_factory=list)
    """(group_id, content)"""
    script_tags_in_head: list[tuple[Optional[dict], str | None]] = field(
        default_factory=list
    )
    """(attrs_dict, content)"""
    script_tags_in_body: list[tuple[Optional[dict], str | None]] = field(
        default_factory=list
    )
    """(attrs_dict, content)"""
    import_map: Optional[dict[str, str]] = None
    icons_svg_path: Optional[Union[Path, Callable[[], Path]]] = None
