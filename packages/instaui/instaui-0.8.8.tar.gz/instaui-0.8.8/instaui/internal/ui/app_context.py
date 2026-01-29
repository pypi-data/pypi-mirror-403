from typing import cast
from contextvars import ContextVar
from ._app import App, DefaultApp


app_var: ContextVar[App] = ContextVar("app_var", default=cast(App, App._default_app))


def get_app() -> App:
    """Get the current App instance from context."""
    app = app_var.get()
    assert app is not None, "No App instance in context"
    return app


def get_current_scope():
    return get_app().get_current_scope()


def get_current_container():
    return get_app().get_current_container()


def get_default_app():
    return cast(DefaultApp, App._default_app)
