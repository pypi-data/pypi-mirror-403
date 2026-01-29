from typing import TypeVar, overload, Any


T = TypeVar("T")
WEB_EVENT_PARAM = object()


@overload
def event_param() -> Any: ...


@overload
def event_param(type_: type[T]) -> T: ...


def event_param(type_: type | None = None):
    """
    Create a placeholder for an event-bound parameter in a UI event handler.

    This function returns a special marker that can be used as the default value
    for a handler parameter in `@ui.event` functions. The actual value of the
    parameter will be injected dynamically when the event is triggered, typically
    via the `params` argument of `component.on()`.

    Args:
        type_ (type | None, optional): Optional Python type hint for the parameter. This can be used for
            type checking or documentation purposes but does not affect runtime
            behavior.

    Example:
    .. code-block:: python

        @ui.event
        def on_click(index = ui.event_param(int)):
            print(f"Clicked on item {index}")

        html.button('Click me').on_click(on_click, params=[42])
    """
    return WEB_EVENT_PARAM


def is_event_param(obj):
    return obj is WEB_EVENT_PARAM
