from dataclasses import dataclass
import inspect
import types
from typing import Callable, List, Any


@dataclass
class DefaultParam:
    name: str
    default: Any


def extract_defaults_and_strip(func: Callable):
    sig = inspect.signature(func)
    defaults: List[DefaultParam] = []
    for p in sig.parameters.values():
        if p.default is not inspect._empty:
            defaults.append(DefaultParam(p.name, p.default))

    if not defaults:
        return [], func

    # new function with no positional defaults
    new_func = types.FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=None,  # key point：remove positional defaults
        closure=func.__closure__,
    )

    # remove keyword-only defaults
    new_func.__kwdefaults__ = None

    new_func.__dict__.update(func.__dict__)
    new_func.__annotations__ = getattr(func, "__annotations__", {}).copy()
    new_func.__doc__ = func.__doc__
    new_func.__module__ = func.__module__

    return defaults, new_func
