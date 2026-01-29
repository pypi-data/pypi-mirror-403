from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Union
from instaui.systems.dataclass_system import dataclass


if TYPE_CHECKING:
    from instaui.internal.runtime.zero_runtime import ZeroRenderResult


@dataclass()
class ReportModel:
    result: ZeroRenderResult

    @property
    def html_size_mb(self) -> float:
        return len(self.result.html.encode("utf-8")) / 1024 / 1024

    @property
    def import_maps_records(self):
        import_maps = (
            self.result.assets.import_maps
            | self.result.options.get_import_maps_cdn_overrides()
        )

        return [
            (
                name,
                str(url) if isinstance(url, Path) else url,
                self._try_get_file_size_mb(url) or "-",
            )
            for name, url in import_maps.items()
        ]

    @property
    def css_links(self):
        return [
            (
                str(link),
                self._path_exists_class(link),
                self._try_get_file_size_mb(link) or "-",
            )
            for link in self.result.assets.css_links
        ]

    @property
    def js_links(self):
        return [
            (
                str(link),
                self._path_exists_class(link),
                self._try_get_file_size_mb(link) or "-",
            )
            for link in self.result.assets.js_links
            if isinstance(link, Path) and link.is_file()
        ]

    @property
    def vue_app_component(self):
        result = []

        for info in self.result.assets.component_dependencies:
            is_file = isinstance(info.esm, Path) and info.esm.is_file()
            class_name = str(self._path_exists_class(info.esm) if is_file else "")
            url = str(info.esm) if is_file else "not file"
            size = self._try_get_file_size_mb(info.esm) if is_file else "-"

            result.append((info.tag_name, url, class_name, size))

        return result

    @property
    def plugins(self):
        result = []

        for info in self.result.assets.plugins:
            is_file = isinstance(info.esm, Path) and info.esm.is_file()
            class_name = str(self._path_exists_class(info.esm) if is_file else "")
            url = str(info.esm) if is_file else "not file"
            size = self._try_get_file_size_mb(info.esm) if is_file else "-"

            result.append((info.name, url, class_name, size))

        return result

    def _try_get_file_size_mb(self, path: Union[str, Path]):
        if isinstance(path, str):
            return None

        return f"{round(path.stat().st_size / 1024 / 1024, 3)} MB"

    def _path_exists_class(self, path: Union[str, Path]):
        if isinstance(path, str):
            return ""
        return "" if path.exists() else NO_EXISTS_PATH_CLASS


class ZeroDebugReporter:
    def generate_report_html(self, result: ZeroRenderResult) -> str:
        from instaui import zero

        return zero().to_html_str(lambda: _create_debug_report(ReportModel(result)))


NO_EXISTS_PATH_CLASS = "ex-no-exists-path"


def _create_debug_report(model: ReportModel):
    from instaui import ui, html

    ui.use_tailwind()
    ui.add_style(rf".{NO_EXISTS_PATH_CLASS} {{background-color: red;color: white;}}")
    box_style = "border-2 border-gray-200 p-4 place-center gap-x-4"

    with ui.column().classes("gap-2"):
        # base info
        with ui.grid(columns="auto 1fr").classes(box_style):
            html.span("file size:")
            html.span(f"{model.html_size_mb:.2f} MB")

        # import maps
        ui.heading("import maps")

        with ui.grid(columns="auto auto auto").classes(box_style):
            ui.text("name")
            ui.text("path or url")
            ui.text("size")

            ui.box(height="1px", width="100%", grid_column="1/-1").style(
                "border-top: 1px solid black;"
            )

            for name, url, size in model.import_maps_records:
                ui.text(name)
                ui.text(url)
                ui.text(size)

        # css links
        ui.heading("css links")

        with ui.grid(columns="1fr auto").classes(box_style):
            ui.text("path or url")
            ui.text("size")

            for link, link_class, size in model.css_links:
                html.span(link).classes(link_class)
                ui.text(size)

        # js links
        ui.heading("js links")
        with ui.column().classes(box_style):
            for link, link_class, size in model.js_links:
                html.span(link).classes(link_class)

        # custom components
        ui.heading("custom components")
        with ui.grid(columns="auto 1fr auto").classes(box_style):
            html.span("name")
            html.span("js file path")
            html.span("size")

            for name, url, class_name, size in model.vue_app_component:
                html.span(name)
                html.span(url).classes(class_name)
                ui.text(size)

        # plguins
        ui.heading("plugins")
        with ui.grid(columns="auto 1fr auto").classes(box_style):
            html.span("name")
            html.span("js file path")
            html.span("size")

            for name, url, class_name, size in model.plugins:
                html.span(name)
                html.span(url).classes(class_name)
                ui.text(size)
