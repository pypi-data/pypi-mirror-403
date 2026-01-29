from pathlib import Path
from typing import Any, Callable, Optional, Union
from instaui.internal.runtime.zero.options import CdnResourceOption, ZeroOptions
from instaui.systems import file_path_system


class ZeroLauncher:
    def __init__(
        self,
        *,
        icons_svg_path: Optional[Union[str, Path, Callable[[], Path]]] = None,
        cdn_resource_overrides: Optional[
            Union[list[CdnResourceOption], CdnResourceOption]
        ] = None,
        debug: bool = False,
    ):
        cdns = (
            cdn_resource_overrides
            if isinstance(cdn_resource_overrides, list)
            else [cdn_resource_overrides]
            if cdn_resource_overrides
            else None
        )

        icons_svg_path = (
            file_path_system.resolve_relative_path(icons_svg_path)
            if isinstance(icons_svg_path, str)
            else icons_svg_path
        )
        self._options = ZeroOptions(debug, icons_svg_path, cdns)

    def to_html(self, render_fn: Callable[..., Any], *, file: Union[str, Path]):
        """
        Generates a static HTML file by rendering the provided function.

        Args:
            render_fn (Callable[..., Any]): A callable that defines the content to be rendered into HTML.
                                        This function typically contains UI component calls.
            file (Union[str, Path]): The output path where the generated HTML file will be saved.
                                    Can be a string or a Path object.

        # Example:
        .. code-block:: python
            from instaui import ui, zero

            def page():
                ui.text("Hello, World!")

            zero().to_html(page, file="output.html")
        """
        file = file_path_system.resolve_relative_path(file)
        file.write_text(self.to_html_str(render_fn), "utf8")

    def to_html_str(self, render_fn: Callable[..., Any]):
        """
        Generates a static HTML file content string by rendering the provided function.

        Args:
            render_fn (Callable[..., Any]): A function that defines the UI content by calling UI components.
                                            It is executed to capture the view structure for static rendering.

        # Example:
        .. code-block:: python
            from instaui import ui, zero

            def page():
                ui.text("Hello, World!")

            html_str = zero().to_html_str(page)
        """
        from instaui.internal.runtime.zero.zero_runtime import ZeroRuntime

        return ZeroRuntime(self._options).run(render_fn)

    def to_debug_report(self, render_fn: Callable[..., Any], *, file: Union[str, Path]):
        """
        Generates a debug report for the static HTML output, including file size and resource usage analysis.

        Args:
            render_fn (Callable[..., Any]): A function that defines the UI content by calling UI components.
                                            It is used to generate the HTML for analysis.
            file (Union[str, Path]): The output file path where the debug report will be saved.

        # Example:
        .. code-block:: python
            from instaui import ui, zero

            def page():
                ui.text("Hello, World!")

            zero().to_debug_report(page, file="debug_report.html")
        """
        file = file_path_system.resolve_relative_path(file)

        # render_result = ZeroRuntime().render_html(render_fn, self._options)

        # file.write_text(
        #     ZeroDebugReporter().generate_report_html(render_result), encoding="utf8"
        # )
