from __future__ import annotations
from contextlib import asynccontextmanager
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Callable, Optional
from enum import Enum
from instaui.systems import file_path_system

if TYPE_CHECKING:
    from fastapi import FastAPI


class WebLauncher:
    def __init__(
        self,
        *,
        debug: bool = False,
        use_gzip: int | bool = True,
        prerender: bool = False,
        prerender_concurrency: int = 4,
    ):
        """
        Create a new server instance.

        Args:
            debug (bool): Whether to run in debug mode. In debug mode, it has the development hot-reload feature. Defaults to False.
            use_gzip (int|bool, optional):  Whether to use gzip compression. If an integer is provided, it will be used as the minimum response size for compression. If True, the default minimum size of 500 bytes will be used. If False, compression will not be used. Defaults to True.
            prerender (bool, optional): Whether to prerender the page. Defaults to False. Note: When debug=True, the prerender option will be ignored (no prerendering will be performed).
            prerender_concurrency (int, optional): The number of concurrent prerendering processes to use. Defaults to 4.
        """
        from instaui.internal.runtime.web.web_runtime import WebRuntime
        from instaui.internal.runtime.web.config import WebUserLaunchConfig

        self.launch_config = WebUserLaunchConfig(
            caller_folder_path=file_path_system.get_caller_path().parent,
            debug=debug,
            use_gzip=use_gzip,
            prerender=prerender,
            prerender_concurrency=prerender_concurrency,
        )

        self._startup_hooks: list[Callable[[], None]] = []
        self._app_hooks: list[Callable[[FastAPI], None]] = []
        self._runtime = WebRuntime(self.launch_config)

    def use(self, fn: Callable[[FastAPI], None]):
        self._app_hooks.append(fn)
        return self

    def add_startup_hook(self, fn: Callable[[], None]):
        self._startup_hooks.append(fn)

    def run(
        self,
        host="0.0.0.0",
        port=8080,
        reload: bool = False,
        reload_dirs: str = ".",
        reload_includes: str = "*.py",
        reload_excludes: str = ".*, .py[cod], .sw.*, ~*",
        log_level="info",
        workers: Optional[int] = None,
        uds: Optional[str] = None,
        **kwargs: Any,
    ):
        from instaui.internal.runtime.web.options import WebUserRunOptions

        if self._startup_hooks:

            @asynccontextmanager
            async def lifespan_wrapper(app):
                for fn in self._startup_hooks:
                    fn()
                yield

            self._runtime.backend.router.lifespan_context = lifespan_wrapper

        opts = WebUserRunOptions(
            app_hooks=self._app_hooks,
            host=host,
            port=port,
            reload=reload,
            reload_dirs=reload_dirs,
            reload_includes=reload_includes,
            reload_excludes=reload_excludes,
            log_level=log_level,
            workers=workers,
            uds=uds,
            kwargs=kwargs,
        )

        self._runtime.run(opts)

    def run_with(
        self,
        app: FastAPI,
        *,
        prefix: str = "/instaui",
        tags: Optional[list[str | Enum]] = None,
        dependencies: Optional[list[Any]] = None,
        responses: Optional[dict[int | str, dict[str, Any]]] = None,
    ):
        """
        Mounts the InstaUI interface onto a FastAPI application with configurable routing.

        Args:
            app (FastAPI): The FastAPI application instance to mount InstaUI onto.
            prefix (str, optional): The URL prefix for InstaUI routes. Defaults to "/instaui".
            tags (Optional[list[str | Enum]], optional): OpenAPI tags for InstaUI endpoints.
            dependencies (Optional[list[Any]], optional): Dependencies to apply to all InstaUI routes.
            responses (Optional[dict[int | str, dict[str, Any]]], optional): Additional response definitions for InstaUI endpoints.

        Example:
        .. code-block:: python
            app = FastAPI()

            @app.get("/")
            def index():
                return {"message": "Hello World"}

            # www.example.com/instaui/ -> InstaUI interface
            @ui.page("/")
            def index_page():
                ui.text("InstaUI page")

            ui.server().run_with(app)


            if __name__ == "__main__":
                import uvicorn
                uvicorn.run(app, host="127.0.0.1", port=8080)

        """
        from fastapi import FastAPI
        from instaui.internal.runtime.web.options import WebUserRunWithOptions
        from instaui.internal.runtime.web.web_runtime import WebRuntime

        runtime = WebRuntime(replace(self.launch_config, prefix=prefix))
        assert isinstance(app, FastAPI), "app must be a FastAPI instance"
        opts = WebUserRunWithOptions(
            app_hooks=self._app_hooks,
            app=app,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
        )

        runtime.run_with(opts)
