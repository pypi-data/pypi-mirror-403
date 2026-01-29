from typing import Any, Callable, TypeVar, cast

from instaui.systems.dataclass_system import dataclass, field
from instaui.internal.ui.app_context import get_app
from instaui.internal.ui.upload import UploadEndpoint
from ._protocols import UploadFileProtocol

THandlerArgs = TypeVar("THandlerArgs", UploadFileProtocol, list[UploadFileProtocol])


@dataclass(frozen=True)
class UploadFileEvent:
    _endpoint: UploadEndpoint = field(init=True)

    @property
    def url(self) -> str:
        return cast(str, self._endpoint)


def upload_file():
    """
    Decorator that registers a file upload handler and returns an upload event object.

    Args:
        handler (Callable[[UploadFileProtocol], Any]): A function that processes uploaded files.
            Takes an UploadFileProtocol object as input and returns any serializable result.

    Returns:
        UploadFileEvent: An event object containing the URL endpoint for file uploads.

    Example:
    .. code-block:: python
        import shutil
        from pathlib import Path
        from instaui import ui, file_io

        @file_io.upload_file()
        def upload_file(file: file_io.TUploadFile) -> file_io.TUploadFileResult:
            save_path = Path(__file__).parent / file.filename

            # read content in chunks(suitable for large files)
            with save_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)

            # read all content(suitable for small files)
            # content = await file.read()
            # save_path.write_bytes(content)

            return {"status": 200, "files": [str(save_path.absolute())]}

        # The upload_file.url can be used in JavaScript to handle file uploads
        print(upload_file.url)
    """

    def wrapper(
        handler: Callable[[THandlerArgs], Any],
    ):
        app = get_app()
        if app.mode == "zero":
            raise Exception("Cannot use upload_file decorator in zero mode.")

        endpoint = UploadEndpoint(handler=handler)
        return UploadFileEvent(endpoint)

    return wrapper
