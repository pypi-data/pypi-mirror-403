from typing import Optional
from instaui.internal.pipeline.utils import html_utils
from instaui.systems.dataclass_system import dataclass, field


@dataclass()
class HtmlRenderContext:
    app_var: str
    lang: str = "en"
    title: str = ""
    favicon_url: str = ""

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
    entry_script_type: str = "module"
    entry_code: str = ""

    mount_id: str = "app"

    import_map: Optional[dict[str, str]] = None

    icons_svg_code: Optional[str] = None

    def render_attrs(self, attrs: Optional[dict]) -> str:
        return html_utils.render_attrs(attrs)
