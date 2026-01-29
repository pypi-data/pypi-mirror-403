from pathlib import Path
from typing import Union
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from urllib.parse import quote

from instaui.internal.backend.fastapi.endpoints import ServerEndpoints
from instaui.internal.ui.file_io._types import TDownloadModeStr


def create_router(router: APIRouter, endpoints: ServerEndpoints):
    @router.get(endpoints.DOWNLOAD_URL)
    def download_file(
        filepath: str = Query(...),
        mode: TDownloadModeStr = Query(None),
        chunk_bytes: Union[int, None] = Query(None),
    ):
        file_path = Path(filepath)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if mode == "chunked":
            return _chunked_download(file_path, chunk_bytes)
        else:
            return _standard_download(file_path)


def _standard_download(file_path: Path) -> Response:
    """Standard non-streaming download"""
    filename = file_path.name
    # support for Chinese filenames
    filename_encoded = quote(filename)
    headers = {
        "Content-Disposition": (
            f"attachment; filename*=UTF-8''{filename_encoded}; filename={filename.encode('utf-8', 'ignore').decode('latin-1')}"
        )
    }

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        headers=headers,
    )


def _chunked_download(
    file_path: Path, chunk_bytes: Union[int, None]
) -> StreamingResponse:
    """Chunked streaming download"""

    chunk_bytes = chunk_bytes or 1024 * 1024  # default to 1MB chunks

    response = StreamingResponse(
        _iter_file(file_path, chunk_bytes), media_type="application/octet-stream"
    )

    encoded_name = quote(file_path.name)
    content_disposition = (
        f"attachment; filename={quote(file_path.stem)}.txt; "
        f"filename*=UTF-8''{encoded_name}"
    )

    response.headers["Content-Disposition"] = content_disposition
    return response


def _iter_file(file_path: Path, chunk_size: int):
    """Helper function to iterate file in chunks"""
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk
