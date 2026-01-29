from typing import Any, Optional, Sequence
from fastapi import HTTPException, Response
from instaui.internal.backend.common.response import response_data
import pydantic


class ResponseData(pydantic.BaseModel):
    values: Optional[list[Any]] = None
    types: Optional[Sequence[int]] = None


def response_web_data(
    outputs_binding_count: int, result: Any, response: Optional[Response] = None
):
    new_result = result
    if response is not None:
        response_interceptor, new_result = _extract_response_interceptor(
            outputs_binding_count, result
        )
        if response_interceptor is not None:
            response_interceptor(response)

    return ResponseData(**response_data(outputs_binding_count, new_result))


def _extract_response_interceptor(outputs_binding_count: int, result: Any):
    if outputs_binding_count == 0:
        if callable(result):
            return result, None
        return None, result

    if outputs_binding_count == 1:
        if isinstance(result, tuple) and len(result) == 2 and callable(result[1]):
            return result[1], result[:-1]
        return None, result

    if (
        isinstance(result, tuple)
        and len(result) - outputs_binding_count == 1
        and callable(result[-1])
    ):
        return result[-1], result[:-1]
    return None, result


class HandlerNotFoundError(HTTPException):
    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(404, detail=message)
