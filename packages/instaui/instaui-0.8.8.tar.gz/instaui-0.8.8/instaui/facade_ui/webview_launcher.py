from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Union
from typing_extensions import Unpack
from instaui.systems import file_path_system
from instaui.internal.runtime.webview.config import PageBuildStrategy

if TYPE_CHECKING:
    from instaui.internal.runtime.webview.options import WebviewStartArgs


class WebViewLauncher:
    """Example usage:
    .. code-block:: python
        from instaui import ui

        @ui.page("/")
        def index_page():
            ui.content("Hello, world!")

        ui.webview().run()
    """

    def __init__(
        self,
        *,
        assets_path: Union[str, Path] = "webview_assets",
        debug: bool = False,
        auto_create_window: Union[bool, str] = "/",
        on_page_mounted: Optional[Callable] = None,
        clean_assets_on_start: bool = True,
        page_build_strategy: PageBuildStrategy = PageBuildStrategy.LAZY,
        prebuild_routes: Optional[list[str]] = None,
    ):
        """Create a new webview wrapper.

        Args:
            assets_path (Path): Path to store assets.
            debug (bool, optional): Whether to run in debug mode. Defaults to False.
            auto_create_window (Union[bool, str], optional): Whether to create a window automatically. If a string is provided, it will be used as the initial page URL. Defaults to "/".
            on_page_mounted (Optional[Callable[[webview.Window], None]], optional): A callback function to be called when the page is mounted. Defaults to None.
            clean_assets_on_start (bool, optional): Whether to clean the assets folder on start. Defaults to True.
            page_build_strategy (PageBuildStrategy, optional): Controls the default page generation behavior for routes not explicitly prebuilt at launch time. Defaults to PageBuildStrategy.LAZY.
            prebuild_routes (Optional[list[str]], optional): An optional list of routes to be generated eagerly at launch, regardless of the default page build strategy. Defaults to None.
        """
        from instaui.internal.runtime.webview.webview_runtime import WebViewRuntime
        from instaui.internal.runtime.webview.config import WebViewUserLaunchConfig

        assets_path = file_path_system.get_caller_path().parent.joinpath(assets_path)

        self.launch_config = WebViewUserLaunchConfig(
            assets_path=assets_path,
            debug=debug,
            auto_create_window=auto_create_window,
            on_page_mounted=on_page_mounted,
            clean_assets_on_start=clean_assets_on_start,
            page_build_strategy=page_build_strategy,
            prebuild_routes=prebuild_routes,
        )

        self._runtime = WebViewRuntime(self.launch_config)

    def create_window(
        self,
        page_url: str = "/",
    ):
        """Create a new window. Returns the window object of pywebview.

        Args:
            page_url (str, optional): Page URL to load. Defaults to "/".

        """
        return self._runtime.create_window(page_url)

    def run(self, **webview_start_args: Unpack[WebviewStartArgs]):
        """Run the webview.

        Args:
            :param func: Function to invoke upon starting the GUI loop.
            :param args: Function arguments. Can be either a single value or a tuple of
                values.
            :param localization: A dictionary with localized strings. Default strings
                and their keys are defined in localization.py.
            :param gui: Force a specific GUI. Allowed values are ``cef``, ``qt``,
                ``gtk``, ``mshtml`` or ``edgechromium`` depending on a platform.
            :param http_server: Enable built-in HTTP server. If enabled, local files
                will be served using a local HTTP server on a random port. For each
                window, a separate HTTP server is spawned. This option is ignored for
                non-local URLs.
            :param user_agent: Change user agent string.
            :param private_mode: Enable private mode. In private mode, cookies and local storage are not preserved.
                Default is True.
            :param storage_path: Custom location for cookies and other website data
            :param menu: List of menus to be included in the app menu
            :param server: Server class. Defaults to BottleServer
            :param server_args: dictionary of arguments to pass through to the server instantiation
            :param ssl: Enable SSL for local HTTP server. Default is False.
            :param icon: Path to the icon file. Supported only on GTK/QT.
        """
        from instaui.internal.runtime.webview.options import WebViewUserRunOptions

        options = WebViewUserRunOptions(webview_start_args=webview_start_args)
        return self._runtime.run(options)

    def _run_with_index(
        self, index_page: Path, webview_start_args: WebviewStartArgs | None = None
    ):
        from instaui.internal.runtime.webview.options import WebViewUserRunOptions

        options = WebViewUserRunOptions(webview_start_args=webview_start_args or {})
        url = str(index_page.absolute())
        return self._runtime._run_with_index(url, options)
