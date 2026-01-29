from enum import Enum
from typing import Any, Callable, Optional, Protocol, Type
from typing_extensions import dataclass_transform
import sys
from dataclasses import (
    dataclass as _dataclass,
    fields,
    Field,
    field as _field,
    asdict as _asdict,
    is_dataclass,
    replace as _replace,
)


PY_VERSION = sys.version_info


field = _field
asdict = _asdict
replace = _replace


@dataclass_transform(field_specifiers=(field,))
def dataclass(
    _cls: Optional[Type[Any]] = None, *, slots: bool = True, **kwargs: Any
) -> Callable[[Type[Any]], Type[Any]]:
    """
    A thin wrapper around dataclasses.dataclass for Python 3.10+.

    Features:
    - slots=True by default
    - Fully equivalent to @dataclass(slots=...)
    - Works with IDE/mypy type hints for smart __init__ completion
    """

    def wrap(cls: Type[Any]) -> Type[Any]:
        return _dataclass(cls, slots=slots, **kwargs)

    if _cls is None:
        # @dataclass(...) usage
        return wrap
    # @dataclass usage
    return wrap(_cls)


class KeyResolver(Protocol):
    def __call__(self, field: Field) -> str: ...


def default_key_resolver(f) -> str:
    return f.name


def metadata_key_resolver(meta_key: str = "key"):
    def _resolver(f) -> str:
        return f.metadata.get(meta_key, f.name)

    return _resolver


def asdict_with_alias(
    obj: Any,
    *,
    key_resolver=default_key_resolver,
) -> Any:
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            key = key_resolver(f)
            value = getattr(obj, f.name)
            result[key] = asdict_with_alias(value, key_resolver=key_resolver)
        return result

    if isinstance(obj, list):
        return [asdict_with_alias(v, key_resolver=key_resolver) for v in obj]

    if isinstance(obj, tuple):
        return tuple(asdict_with_alias(v, key_resolver=key_resolver) for v in obj)

    if isinstance(obj, dict):
        return {
            k: asdict_with_alias(v, key_resolver=key_resolver) for k, v in obj.items()
        }

    return obj


def asdict_no_none(obj, *, key_resolver=default_key_resolver) -> dict:
    def _clean(v: Any):
        if isinstance(v, Enum):
            return v.value

        if is_dataclass(v):
            return _clean(asdict(v))  # type: ignore
        if isinstance(v, dict):
            return {k: _clean(vv) for k, vv in v.items() if vv is not None}
        if isinstance(v, list):
            return [_clean(i) for i in v]
        return v

    return _clean(asdict_with_alias(obj, key_resolver=key_resolver))  # type: ignore
