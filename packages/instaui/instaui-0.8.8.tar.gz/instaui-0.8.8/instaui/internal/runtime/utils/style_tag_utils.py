from instaui.internal.assets.style_assets import StyleTag


def gen_style_tag_group_id_attr(style_tag: StyleTag) -> str:
    if style_tag.group_id:
        return f' data-instaui-group-id="{style_tag.group_id}"'

    return ""
