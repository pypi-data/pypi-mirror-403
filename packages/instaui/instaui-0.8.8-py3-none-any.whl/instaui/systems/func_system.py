import inspect
from pathlib import Path
from typing import Callable, Tuple, get_type_hints


def get_fn_params_infos(fn: Callable) -> list[Tuple[str, type]]:
    """Get the parameter names and types of a function

    Args:
        fn (function): _description_

    Returns:
        [('a', int), ('b', str)]
    """
    signature = inspect.signature(fn)
    type_hints = get_type_hints(fn)

    return [
        (name, type_hints.get(name, inspect._empty))
        for name in signature.parameters.keys()
    ]


def is_last_param_args(fn):
    """
    Returns:
        bool: True if the last parameter of the function is `*args`, False otherwise.
    """
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())

    if not params:
        return False

    last_param = params[-1]
    return last_param.kind == inspect.Parameter.VAR_POSITIONAL


def get_function_location_info(func) -> Tuple[str, int, str]:
    """

    Returns:
        Tuple[str, int, str]: A tuple containing the file path, start line number, and function name.
    """
    file_path = inspect.getfile(func)
    _, start_line = inspect.getsourcelines(func)

    return str(Path(file_path).resolve()), start_line, func.__qualname__
