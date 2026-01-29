import inspect
from typing import Any, Callable, Literal, Optional, Sequence
from instaui.internal.ast import expression
from instaui.internal.ui.enums import InputBindingType
from instaui.internal.ui.input_slient_data import InputSilentData
from instaui.internal.ui.protocol import (
    CanInputProtocol,
    CanOutputProtocol,
    ObservableProtocol,
)

_SYNC_TYPE = "sync"
_ASYNC_TYPE = "async"


def normalize_f_type(f_type: Optional[Literal["async", "sync"]]):
    if f_type is None or f_type == "sync":
        return None

    return f_type


def inputs_to_types(inputs: Sequence[Any]):
    return [
        input._to_event_input_type().value
        if isinstance(input, CanInputProtocol)
        else InputBindingType.Data.value
        for input in inputs
    ]


def outputs_to_types(outputs: Sequence[CanOutputProtocol]):
    return [output._to_event_output_type().value for output in outputs]


def analyze_observable_inputs(
    inputs: Sequence,
) -> tuple[list, list[int], list[int]]:
    """
    Returns:
        inputs, slients, datas
    """

    slients: list[int] = [0] * len(inputs)
    datas: list[int] = [0] * len(inputs)
    result_inputs = []

    for idx, input in enumerate(inputs):
        if isinstance(input, ObservableProtocol):
            result_inputs.append(input)
            continue

        elif isinstance(input, CanInputProtocol):
            slients[idx] = 1
            result_inputs.append(
                input.value if isinstance(input, InputSilentData) else input
            )

        elif input is None:
            result_inputs.append(expression.UNDEFINED)
            datas[idx] = 1

        else:
            datas[idx] = 1
            result_inputs.append(input)

    return result_inputs, slients, datas


def py_function_type(fn: Callable):
    return _ASYNC_TYPE if inspect.iscoroutinefunction(fn) else _SYNC_TYPE


def normalize_int_values(values: Optional[Sequence[int]], by: int = 0):
    if not values:
        return None

    if all(x == by for x in values):
        return None

    return values
