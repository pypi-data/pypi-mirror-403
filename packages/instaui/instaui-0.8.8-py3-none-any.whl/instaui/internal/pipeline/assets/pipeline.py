from itertools import chain, groupby
from pathlib import Path
from instaui.internal.assets.base import AssetsDeclaration
from instaui.internal.assets.component_dep import ComponentDependencyRegistry
from instaui.internal.assets.css_assets import CssAssetCollection
from instaui.internal.assets.script_assets import JSAsset
from instaui.internal.assets.snapshot import (
    AssetsSnapshot,
    ComponentDependencySnapshot,
    ScriptTagSnapshot,
)
from instaui.internal.assets.style_assets import StyleTag
from .processors.base import AssetsProcessor


class AssetsPipeline:
    def __init__(self, processors: list[AssetsProcessor]):
        self._processors = processors

    def run(
        self, global_assets: AssetsDeclaration, local_assets: AssetsDeclaration
    ) -> AssetsSnapshot:
        merged = self.merge(global_assets, local_assets)

        for processor in self._processors:
            processor.process(merged)

        script_tags_in_head = [
            _convert_script_tag(js_asset)
            for js_asset in merged.js_asset
            if js_asset.position == "head"
        ]

        script_tags_in_body = [
            _convert_script_tag(js_asset)
            for js_asset in merged.js_asset
            if js_asset.position == "body"
        ]

        return AssetsSnapshot(
            css_links=list(merged.css_links.iter_css_links()),
            style_tags=merged.style_tags,
            script_tags_in_head=script_tags_in_head,
            script_tags_in_body=script_tags_in_body,
            import_maps=merged.import_maps,
            favicon=merged.favicon,
            plugins=merged.plugins,
            component_dependencies=_convert_component_snapshot(
                merged.component_dependencies
            ),
        )

    def merge(
        self, global_assets: AssetsDeclaration, local_assets: AssetsDeclaration
    ) -> AssetsDeclaration:
        assert local_assets is not None, "should be called inside a page() context"

        plugins = global_assets.plugins | local_assets.plugins

        component_dependencies = ComponentDependencyRegistry()

        for record in chain(
            global_assets.component_dependencies.records,
            local_assets.component_dependencies.records,
        ):
            component_dependencies.add(record.component, record.dependency)

        css_links = CssAssetCollection.merge(
            global_assets.css_links, local_assets.css_links
        )
        style_tags = _merged_style_tags(
            global_assets.style_tags, local_assets.style_tags
        )
        script_tags = global_assets.js_asset + local_assets.js_asset
        import_maps = {**global_assets.import_maps, **local_assets.import_maps}
        favicon = global_assets.favicon or (
            local_assets.favicon if local_assets else None
        )

        component_extensions = global_assets.component_extensions.overridden_by(
            local_assets.component_extensions
        )

        return AssetsDeclaration(
            css_links=css_links,
            style_tags=style_tags,
            js_asset=script_tags,
            import_maps=import_maps,
            favicon=favicon,
            plugins=plugins,
            component_dependencies=component_dependencies,
            component_extensions=component_extensions,
        )


def _merged_style_tags(global_tags: list[StyleTag], local_tags: list[StyleTag]):
    tags = global_tags + local_tags
    sorted_tags = sorted(tags, key=lambda tag: tag.group_id or "")

    return [
        StyleTag("\n".join(tag.content for tag in group_tags), group_id=group_id)
        for group_id, group_tags in groupby(sorted_tags, lambda tag: tag.group_id)
    ]


def _convert_component_snapshot(
    registry: ComponentDependencyRegistry,
) -> list[ComponentDependencySnapshot]:
    return [
        ComponentDependencySnapshot(
            tag=record.dependency.tag_name,
            esm=record.dependency.esm,
        )
        for record in registry.records
    ]


def _convert_script_tag(asset: JSAsset):
    inline_code = (
        _js_source_to_inline_code(asset.source) if asset.kind == "inline" else None
    )

    attrs = dict(asset.attrs)

    if asset.kind != "inline":
        attrs["src"] = asset.source

    if asset.module:
        attrs["type"] = "module"

    if asset.loading == "async":
        attrs["async"] = True
    elif asset.loading == "defer":
        attrs["defer"] = True

    return ScriptTagSnapshot(
        attrs=attrs,
        inline_code=inline_code,
    )


def _js_source_to_inline_code(source: str | Path):
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")

    return source
