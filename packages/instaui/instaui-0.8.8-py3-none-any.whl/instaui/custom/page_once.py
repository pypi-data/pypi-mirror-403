from functools import wraps
from typing import Callable
from instaui.internal.ui.page_once import run_page_once


def page_once(
    func: Callable | None = None,
    *,
    key: str | None = None,
    namespace: str | None = None,
):
    """
    Executes a function at most once during a single page construction lifecycle.

    This decorator is intended to be used inside component constructors or page
    functions to register logic that should run only once per page render, even if
    the surrounding component is instantiated multiple times.

    Typical use cases include injecting JavaScript or CSS assets, registering global
    event handlers, or performing other one-time setup operations scoped to the
    current page.

    Args:
        func (Callable | None): The function to execute once. If None, the decorator
            returns a partially applied decorator for later use.
        key (str | None): An optional unique identifier used to deduplicate execution.
            Functions with the same key will be executed only once per page lifecycle.
            If not provided, a key will be automatically derived from the function's
            qualified name.
        namespace (str | None): Optional namespace used to isolate execution keys between
            different libraries or plugins. It is strongly recommended for plugin authors
            to set this value to their package or plugin name to avoid collisions.


    Example:
    .. code-block:: python
        from instaui import custom

        class CustomComponent(custom.element):
            def __init__(self):
                super().__init__()

                @custom.page_once
                def inject_runtime():
                    self.add_js("console.log('loaded')")


        # With explicit key for cross-component deduplication
        @custom.page_once(key="shiki_runtime")
        def install_shiki():
            load_shiki_assets()

    Notes:
        - The function is executed immediately at decoration time.
        - The execution is scoped to the current page context and isolated between
          different page renders and user sessions.
        - Calling this decorator outside of a page context will raise an error.
    """
    if func is None:
        return lambda f: page_once(f, key=key, namespace=namespace)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_page_once(
            lambda: func(*args, **kwargs),
            key=key,
            namespace=namespace,
        )

    # execute immediately
    wrapper()

    return wrapper
