from typing import Callable
from instaui.internal.ui.app_context import get_app


def run_page_once(func: Callable[[], None], key=None, namespace: str | None = None):
    app = get_app()
    if app is None:
        raise RuntimeError("custom.page_once must be called inside a page function")

    once_key = make_once_key(func, key, namespace)

    if once_key in app._page_once_registry:
        return False

    app._page_once_registry.add(once_key)
    func()
    return True


def make_once_key(
    func: Callable[[], None], key: str | None = None, namespace: str | None = None
) -> str:
    if namespace is None:
        namespace = func.__module__

    if key is None:
        key = func.__qualname__

    return f"{namespace}:{key}"
