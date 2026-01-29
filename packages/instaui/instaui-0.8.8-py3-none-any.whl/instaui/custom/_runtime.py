from instaui.constants.runtime import RuntimeMode
from instaui.internal.context.page_context import in_page_context
from instaui.internal.ui.app_context import get_app


class RuntimeCtx:
    def _app(self):
        assert in_page_context(), "Should be used inside ui.page() context"
        app = get_app()
        return app

    @property
    def mode(self):
        return self._app().mode

    @property
    def is_web(self) -> bool:
        return self.mode == RuntimeMode.WEB

    @property
    def is_webview(self) -> bool:
        return self.mode == RuntimeMode.WEBVIEW

    @property
    def is_zero(self) -> bool:
        return self.mode == RuntimeMode.ZERO

    @property
    def is_debug(self):
        return self._app().debug_mode


runtime_ctx = RuntimeCtx()
