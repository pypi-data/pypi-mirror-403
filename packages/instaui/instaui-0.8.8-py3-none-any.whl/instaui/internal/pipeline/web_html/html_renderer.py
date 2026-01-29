from __future__ import annotations
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader
from instaui.internal.codegen.program_codegen import CodegenResult
from .html_context import HtmlRenderContext


class WebHtmlRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, codegen: CodegenResult, options: HtmlOptions) -> str:
        template = self.env.get_template("web.html.j2")

        ctx = HtmlRenderContext(
            app_var=codegen.app_var,
            is_debug=options.is_debug,
            title=options.title,
            favicon_url=options.favicon_url,
            prefix=options.prefix,
            css_links=options.css_links,
            style_tags=options.style_tags,
            script_tags_in_head=options.script_tags_in_head,
            script_tags_in_body=options.script_tags_in_body,
            entry_code=codegen.entry_code,
            import_map=options.import_map if options.import_map else None,
            icons_svg_code=options.icons_svg_code,
        )

        return template.render(model=ctx)


@dataclass()
class HtmlOptions:
    is_debug: bool
    favicon_url: str
    title: str = "instaui"
    prefix: str = ""

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
    icons_svg_code: Optional[str] = None
