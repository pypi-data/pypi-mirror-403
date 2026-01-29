from typing import Any, cast
import webview
from instaui.internal.backend.base import BaseBackend
from instaui.internal.backend.common import python_handler_utils
from instaui.internal.backend.invocation import BackendInvocation, BackendInvocationKind
from instaui.internal.runtime.webview.config import WebViewUserLaunchConfig
from instaui.internal.runtime.webview.options import WebViewUserRunOptions
from instaui.protocol.invocation.spec import ComputedSpec, EventSpec
from .watch_handler import register_watch_handler
from .event_handler import register_event_handler
from . import api


class WebViewBackend(BaseBackend):
    def __init__(self, config: WebViewUserLaunchConfig) -> None:
        self.launch_config = config

    def create_window(
        self,
        url: str,
    ):
        """Create a new window. Returns the window object of pywebview."""
        window = webview.create_window(self.launch_config.title, url, js_api=api.Api())

        if self.launch_config.on_page_mounted:

            def on_app_mounted():
                self.launch_config.on_page_mounted(window)  # type: ignore

            window.expose(on_app_mounted)

        return window

    def run(self, run_options: WebViewUserRunOptions):
        webview.start(**run_options.webview_start_args, debug=self.launch_config.debug)

    def _run_with_index(
        self, index_url: str, run_options: WebViewUserRunOptions | None
    ):
        webview.create_window(self.launch_config.title, index_url, js_api=api.Api())

        opts = {}
        if run_options:
            opts.update(run_options.webview_start_args)

        opts.update({"debug": self.launch_config.debug})

        webview.start(**opts)

    def register_invocation(self, ref_id: int, invocation: BackendInvocation) -> Any:
        route = invocation.render_ctx.route
        assert route is not None, "route must be set in render_ctx for invocation"

        if (
            invocation.kind == BackendInvocationKind.COMPUTED
            or invocation.kind == BackendInvocationKind.WATCH
        ):
            spec = cast(ComputedSpec, invocation.spec)

            key = python_handler_utils.create_handler_key(
                route, invocation.fn, self.launch_config.debug, extra_key=spec.extra_key
            )
            register_watch_handler(
                key,
                invocation.fn,
                spec.outputs_binding_count,
                spec.custom_type_adapter_map,
            )

            return key

        if invocation.kind == BackendInvocationKind.EVENT:
            spec = cast(EventSpec, invocation.spec)

            key = python_handler_utils.create_handler_key(
                route, invocation.fn, self.launch_config.debug, extra_key=spec.extra_key
            )

            register_event_handler(
                key,
                invocation.fn,
                spec.outputs_binding_count,
                spec.dataset_input_indexs,
                spec.custom_type_adapter_map,
            )

            return key

        if invocation.kind == BackendInvocationKind.FILE_UPLOAD:
            raise NotImplementedError
            # file_upload_router.register_upload_file_handler(
            #     key, invocation.fn, self.endpoints.UPLOAD_URL_WITH_PREFIX
            # )

            # return f"{self.endpoints.UPLOAD_URL_WITH_PREFIX}?hkey={key}"
