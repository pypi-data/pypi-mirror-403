from typing import Any, Callable, List, Tuple, TypeVar, cast


# ---------- Operation Utilities ----------


def remove_none(key: str, value: Any) -> Tuple[str, Any, bool]:
    """
    Operation: remove entries with None values.
    Return (key, value, keep_entry)
    """
    return key, value, value is not None


def remove_empty_collection(key: str, value: Any) -> Tuple[str, Any, bool]:
    """
    Operation: remove entries with empty collections.
    """
    return key, value, (not isinstance(value, (list, dict))) or len(value) > 0


def repr_dict_keys(key: str, value: Any) -> Tuple[str, Any, bool]:
    return repr(key), value, True


# ---------- Core Processor ----------

_TData = TypeVar("_TData")


def process_dict(
    data: _TData,
    operations: List[Callable[[str, Any], Tuple[str, Any, bool]]],
    *,
    recursive: bool = True,
) -> _TData:
    """
    Apply multiple operations to a dictionary efficiently.
    operations: list of functions(key, value) -> (new_key, new_value, keep)
    """

    if not isinstance(data, dict):
        return data

    output = {}

    for key, value in data.items():
        original_key = key
        original_value = value

        # Recursively process nested data
        if recursive:
            if isinstance(value, dict):
                value = process_dict(value, operations, recursive=True)
            elif isinstance(value, list):
                value = _process_list(value, operations, recursive)

        # Apply operations sequentially
        keep = True
        for op in operations:
            key, value, keep = op(key, value)
            if not keep:
                break

        if keep:
            output[key] = value
        else:
            # Reset key/value so next item does not get affected accidentally
            key, value = original_key, original_value

    return cast(_TData, output)


def _process_list(
    data_list: List[Any], operations: List[Callable], recursive: bool
) -> List[Any]:
    result = []
    for item in data_list:
        if isinstance(item, dict):
            result.append(process_dict(item, operations, recursive=True))
        elif isinstance(item, list) and recursive:
            result.append(_process_list(item, operations, recursive=True))
        else:
            result.append(item)
    return result
