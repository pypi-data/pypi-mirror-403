from __future__ import annotations

import asyncio
import inspect
import logging
import multiprocessing
import os
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Final, Optional, Set, cast

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from uvicorn.supervisors import ChangeReload

import __main__
from instaui.internal.backend.base import AssetBackendMixin, BaseBackend
from instaui.internal.backend.common import python_handler_utils
from instaui.internal.backend.fastapi.endpoints import ServerEndpoints
from instaui.internal.backend.fastapi.page_cache import PageCache
from instaui.internal.backend.invocation import BackendInvocation, BackendInvocationKind
from instaui.internal.router.model import PageInfo
from instaui.internal.router.registry import route_registry
from instaui.internal.runtime.logging import setup_instaui_logging
from instaui.protocol.invocation.spec import ComputedSpec, EventSpec

from . import (
    asset_mapper,
    debug_mode_router,
    dependency_router,
    event_router,
    file_download_router,
    file_upload_router,
    watch_router,
)
from ._uvicorn import UvicornServer
from .middlewares import NoCacheDebugModeMiddleware, RequestContextMiddleware

if TYPE_CHECKING:
    from instaui.internal.runtime.web.config import WebUserLaunchConfig
    from instaui.internal.runtime.web.options import (
        WebUserRunOptions,
        WebUserRunWithOptions,
    )
    from instaui.internal.runtime.web.runtime_services import WebRuntimeServices

APP_IMPORT_STRING: Final[str] = (
    "instaui.internal.backend.fastapi.web_backend:FastapiBackend.app"
)


class FastapiBackend(BaseBackend, AssetBackendMixin):
    app: Optional[FastAPI] = None

    def __init__(
        self,
        *,
        config: WebUserLaunchConfig,
        user_assets_dir: Optional[Path] = None,
        runtimie_services: WebRuntimeServices,
    ):
        self._config = config
        self._debug_mode = config.debug
        self._use_gzip = config.use_gzip
        self._user_assets_dir = user_assets_dir
        self._router = APIRouter(tags=["InstaUI"], prefix=config.prefix)
        self.endpoints = ServerEndpoints(config.prefix)
        self._runtimie_services = runtimie_services

        dependency_router.create_router(self._router, self.endpoints)
        event_router.create_router(self._router, self._debug_mode, self.endpoints)
        watch_router.create_router(self._router, self._debug_mode, self.endpoints)
        file_upload_router.create_router(self._router, self.endpoints)
        file_download_router.create_router(self._router, self.endpoints)
        debug_mode_router.create_router(self._router, self._debug_mode)

        for path, info in route_registry.routes.items():
            self.register_page(path, info)

        self._registered_static_routes: Set[str] = set()
        self._page_cache = PageCache()
        self._logger = logging.getLogger(__name__)

    @property
    def router(self) -> APIRouter:
        return self.app.router if self.app else self._router

    def register_dynamic_page(self, path: str, fn: Callable, *, cache: bool = False):
        """
        For dynamic page registration after service startup"""
        info = PageInfo(fn, cache)
        route_registry.add_route(path, info)
        self.register_page(path, info)

    def register_page(self, path: str, info: PageInfo):
        """
        For page registration before service startup. After service startup, use register_dynamic_page for registration
        """
        is_async = inspect.iscoroutinefunction(info.fn)

        self._remove_route(path)

        if is_async:

            @self.router.get(path)
            async def _(request: Request):
                html = await self._page_cache.get_or_render_async(
                    key=path,
                    cache=(not self._debug_mode) and info.cache,
                    render=lambda: self._runtimie_services.render_fn_async(path),
                )

                return HTMLResponse(html)

        else:

            @self.router.get(path)
            def _(request: Request):
                html = self._page_cache.get_or_render_sync(
                    key=path,
                    cache=(not self._debug_mode) and info.cache,
                    render=lambda: self._runtimie_services.render_fn(path),
                )

                return HTMLResponse(html)

    def _remove_route(self, path: str) -> None:
        self.router.routes[:] = [
            r for r in self.router.routes if getattr(r, "path", None) != path
        ]

    def try_close_server(self):
        assert UvicornServer.get_instance() is not None, (
            "Uvicorn server does not exist. Cannot attempt to shut down service in debug mode or reload mode"
        )
        UvicornServer.get_instance().should_exit = True

    def run(self, options: WebUserRunOptions):
        setup_instaui_logging(debug=self._debug_mode)
        reload = self._debug_mode or options.reload

        app = FastAPI()
        FastapiBackend.app = app
        self._setup_fastapi_app(app, app_hooks=options.app_hooks)

        if (not self._debug_mode) and self._config.prerender:
            self.prerender_all_pages()

        if multiprocessing.current_process().name != "MainProcess":
            return

        if reload and not hasattr(__main__, "__file__"):
            reload = False

        config = uvicorn.Config(
            APP_IMPORT_STRING if reload else app,
            host=options.host,
            port=options.port,
            reload=reload,
            log_level=options.log_level,
            workers=options.workers,
            uds=options.uds,
            reload_includes=_split_args(options.reload_includes) if reload else None,
            reload_excludes=_split_args(options.reload_excludes) if reload else None,
            reload_dirs=_split_args(options.reload_dirs) if reload else None,
            **options.kwargs,
        )

        UvicornServer.create_singleton(config, [debug_mode_router.when_server_reload])

        if config.should_reload:
            ChangeReload(
                config, target=UvicornServer.get_instance().run, sockets=[]
            ).run()
        else:
            UvicornServer.get_instance().run()

        if config.uds:
            os.remove(config.uds)  # pragma: py-win32

    def run_with(self, options: WebUserRunWithOptions):
        """
        Mounts the InstaUI interface onto a FastAPI application with configurable routing.
        """

        assert isinstance(options.app, FastAPI), "app must be a FastAPI instance"

        if options.tags is not None:
            self._router.tags = options.tags
        if options.dependencies:
            self._router.dependencies = options.dependencies
        if options.responses:
            self._router.responses = options.responses

        self._setup_fastapi_app(
            options.app, include_router=False, app_hooks=options.app_hooks
        )

        if (not self._debug_mode) and self._config.prerender:
            self.prerender_all_pages()

        options.app.include_router(self._router)
        return self._router

    def _setup_fastapi_app(
        self,
        app: FastAPI,
        *,
        include_router=True,
        app_hooks: list[Callable[[FastAPI], None]],
    ):
        app.add_middleware(RequestContextMiddleware, debug=self._debug_mode)
        if self._debug_mode:
            app.add_middleware(NoCacheDebugModeMiddleware)

        if self._use_gzip:
            app.add_middleware(
                GZipMiddleware,
                minimum_size=self._use_gzip if isinstance(self._use_gzip, int) else 500,
            )

        for fn in app_hooks:
            fn(app)

        app.mount(
            self.endpoints.INSTAUI_STATIC_URL,
            StaticFiles(directory=self.endpoints.STATIC_DIR),
            name=self.endpoints.INSTAUI_STATIC_URL,
        )

        if include_router:
            app.include_router(self._router)

        if self._user_assets_dir:
            app.mount(
                self.endpoints.INSTAUI_USER_ASSETS_URL_WITH_PREFIX,
                StaticFiles(directory=self._user_assets_dir),
            )
            self._logger.info(
                f"User assets directory found: {self._user_assets_dir} : mount to {self.endpoints.INSTAUI_USER_ASSETS_URL}"
            )

    def prerender_all_pages(self):
        """
        Render all cacheable pages before server start.
        """
        routes = [
            (path, info) for path, info in route_registry.routes.items() if info.cache
        ]

        if not routes:
            self._logger.info("prerender skipped: no cacheable pages found")
            return

        self._logger.info("prerender start: %d pages", len(routes))

        async_tasks: list[tuple[str, Awaitable[None]]] = []

        for path, info in routes:
            is_async = inspect.iscoroutinefunction(info.fn)

            if is_async:
                async_tasks.append((path, self._prerender_async_page(path)))
            else:
                self._prerender_sync_page(path)

        if async_tasks:
            self._run_async_prerender(async_tasks)

        self._logger.info("prerender finished: %d pages", len(routes))

    def _prerender_sync_page(self, path: str):
        start = time.perf_counter()
        try:
            html = self._runtimie_services.render_fn(path)
            self._page_cache.warmup(path, html)

            elapsed = (time.perf_counter() - start) * 1000
            self._logger.debug(
                "prerender sync page success: path=%s elapsed=%.2fms",
                path,
                elapsed,
            )

        except Exception:
            self._logger.exception(
                "prerender sync page failed: path=%s",
                path,
            )

    async def _prerender_async_page(self, path: str):
        start = time.perf_counter()
        try:
            html = await self._runtimie_services.render_fn_async(path)
            self._page_cache.warmup(path, html)
            elapsed = (time.perf_counter() - start) * 1000
            self._logger.debug(
                "prerender async page success: path=%s elapsed=%.2fms",
                path,
                elapsed,
            )

        except Exception:
            self._logger.exception(
                "prerender async page failed: path=%s",
                path,
            )

    def _run_async_prerender(self, tasks: list[tuple[str, Awaitable[None]]]):
        async def runner():
            await asyncio.gather(*(task for _, task in tasks))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(runner())
            self._logger.debug("prerender async tasks scheduled in running loop")
        else:
            asyncio.run(runner())

    def register_invocation(self, ref_id: int, invocation: BackendInvocation) -> Any:
        route = invocation.render_ctx.route
        assert route is not None, "route must be set in render_ctx for invocation"

        if (
            invocation.kind == BackendInvocationKind.COMPUTED
            or invocation.kind == BackendInvocationKind.WATCH
        ):
            spec = cast(ComputedSpec, invocation.spec)
            key = python_handler_utils.create_handler_key(
                route, invocation.fn, self._debug_mode, extra_key=spec.extra_key
            )
            watch_router.register_watch_handler(
                key,
                invocation.fn,
                spec.outputs_binding_count,
                spec.custom_type_adapter_map,
            )

            return key

        if invocation.kind == BackendInvocationKind.EVENT:
            spec = cast(EventSpec, invocation.spec)

            key = python_handler_utils.create_handler_key(
                route, invocation.fn, self._debug_mode, extra_key=spec.extra_key
            )

            event_router.register_event_handler(
                key,
                invocation.fn,
                spec.outputs_binding_count,
                spec.dataset_input_indexs,
                spec.custom_type_adapter_map,
            )

            return key

        if invocation.kind == BackendInvocationKind.FILE_UPLOAD:
            key = python_handler_utils.create_handler_key(
                route, invocation.fn, self._debug_mode
            )

            file_upload_router.register_upload_file_handler(
                key, invocation.fn, self.endpoints.UPLOAD_URL_WITH_PREFIX
            )

            return f"{self.endpoints.UPLOAD_URL_WITH_PREFIX}?hkey={key}"

    def register_asset(self, path: Path) -> str:
        return asset_mapper.record_asset(path, self.endpoints)


def _split_args(args: str):
    return [a.strip() for a in args.split(",")]
