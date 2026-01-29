from __future__ import annotations
import threading
from typing import TYPE_CHECKING, Callable, Optional
from fastapi import APIRouter, Request, UploadFile, Query, File
from starlette.datastructures import UploadFile as StarletteUploadFile
from .systems import async_system
from instaui.internal.backend.common import handler as _handler


if TYPE_CHECKING:
    from .endpoints import ServerEndpoints


_event_handlers: dict[str, _handler.HandlerInfo] = {}
dict_lock = threading.Lock()


def create_router(router: APIRouter, endpoints: ServerEndpoints):
    @router.post(endpoints.UPLOAD_URL)
    async def _(
        request: Request,
        hkey: str = Query(...),
        files: list[UploadFile] = File(None),
        file: UploadFile = File(None),
    ):
        handler = _get_handler(hkey)
        if handler is None:
            raise ValueError("event handler not found")

        real_file = await _convert_file(request, files, file)
        return await async_system.maybe_async(handler.fn, real_file)


def _get_handler(hkey: str):
    return _event_handlers.get(hkey)


async def _convert_file(
    request: Request,
    files: Optional[list[UploadFile]] = None,
    file: Optional[UploadFile] = None,
):
    if file:
        return file
    if files:
        return files

    form = await request.form()
    indexed_files = []
    for key, value in form.multi_items():
        if key.startswith("file["):
            if isinstance(value, StarletteUploadFile):
                indexed_files.append(value)

    return indexed_files


def register_upload_file_handler(key: str, handler: Callable, upload_url: str):
    upload_url = f"{upload_url}?hkey={key}"

    if key in _event_handlers:
        return upload_url

    handler_info = _handler.HandlerInfo.from_handler(
        handler,
        0,
        skip_convert_param=True,
    )

    with dict_lock:
        _event_handlers[key] = handler_info

    return upload_url
