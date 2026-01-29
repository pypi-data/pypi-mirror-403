from contextlib import ExitStack, contextmanager
from typing import Optional

from instaui.constants.runtime import RuntimeMode
from instaui.internal.assets import enter_assets_context
from instaui.internal.context.page_context import enter_page_context

from ._app import App, DefaultApp
from ._scope import Scope
from .app_context import app_var, get_app


@contextmanager
def new_app(
    mode: RuntimeMode,
    *,
    debug: bool,
    meta: Optional[dict] = None,
):
    app = App(
        mode=mode,
        debug=debug,
        meta=meta,
    )
    token = app_var.set(app)
    app_scope = Scope()

    with ExitStack() as stack:
        stack.callback(app_var.reset, token)
        stack.enter_context(enter_page_context())
        stack.enter_context(enter_assets_context())
        stack.enter_context(app_scope)
        yield app


def check_default_app_slot_or_error(
    error_message="Operations are not allowed outside of ui.page",
):
    if isinstance(get_app(), DefaultApp):
        raise ValueError(error_message)


def new_scope_if_needed() -> None:
    ctx = get_app()

    if ctx.has_pending_scope():
        pending = ctx.top_pending_scope()

        if not pending.realized:
            container = ctx.get_current_container()
            scope = Scope()
            scope.__enter__()
            container.add_child(scope)
            container._bind_scope(scope)
            pending.realized = True
