from .registry import route_registry
from .model import PageInfo


def page(path: str, *, cache: bool = True):
    """
    Decorator for page registration.

    Args:
        path (str): Path of the page.
        cache (bool, optional): Whether to cache the page or not. Defaults to True.
            Note: When path contains parameters (e.g. '/{name}'), cache should be set to False
            as parameterized paths typically serve dynamic content that shouldn't be cached.

    Example:
    .. code-block:: python
        from instaui import ui

        @ui.page('/')
        def home():
            ui.text('Hello, world!')

        @ui.page('/about')
        def about():
            ui.text('About us')

        @ui.page('/{name}', cache=False)
        def user():
            name = ui.param('name')
            ui.text(name)
    """

    def decorator(func):
        route_registry.add_route(path, PageInfo(func, cache))
        return func

    return decorator
