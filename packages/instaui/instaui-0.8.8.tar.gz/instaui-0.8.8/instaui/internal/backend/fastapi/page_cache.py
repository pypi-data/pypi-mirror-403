import asyncio
import threading
from collections import defaultdict
from typing import Callable, Awaitable


class PageCache:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

        self._async_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._sync_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    # ---------- async ----------
    async def get_or_render_async(
        self,
        *,
        key: str,
        cache: bool,
        render: Callable[[], Awaitable[str]],
    ) -> str:
        if not cache:
            return await render()

        # fast path
        html = self._cache.get(key)
        if html is not None:
            return html

        lock = self._async_locks[key]
        async with lock:
            # double check
            html = self._cache.get(key)
            if html is not None:
                return html

            html = await render()
            self._cache[key] = html
            return html

    # ---------- sync ----------
    def get_or_render_sync(
        self,
        *,
        key: str,
        cache: bool,
        render: Callable[[], str],
    ) -> str:
        if not cache:
            return render()

        # fast path
        html = self._cache.get(key)
        if html is not None:
            return html

        lock = self._sync_locks[key]
        with lock:
            # double check
            html = self._cache.get(key)
            if html is not None:
                return html

            html = render()
            self._cache[key] = html
            return html

    def warmup(self, key: str, html: str):
        self._cache[key] = html
