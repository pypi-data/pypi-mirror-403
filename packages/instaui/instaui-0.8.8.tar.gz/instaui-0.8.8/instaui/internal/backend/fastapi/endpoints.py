from pathlib import Path
from instaui.constants.ui import USER_ASSETS_DIR_NAME, USER_ASSETS_ICONS_DIR_NAME
from instaui.version import __version__ as _INSTA_VERSION
from instaui.resources import (
    APP_CSS_PATH,
    APP_ES_JS_PATH,
    FAVICON_PATH,
    STATIC_DIR,
    VUE_ES_JS_PATH,
)

RUNTIME_API_PREFIX = "/api/_internal"


class ServerEndpoints:
    def __init__(self, prefix: str = ""):
        self.prefix = self._normalize_prefix(prefix)

        self.INSTAUI_STATIC_URL = f"/_instaui_{_INSTA_VERSION}/static"
        self.INSTAUI_STATIC_URL_WITH_PREFIX = self.with_prefix(self.INSTAUI_STATIC_URL)
        self.INSTAUI_USER_ASSETS_URL = f"/_internal/{USER_ASSETS_DIR_NAME}"
        self.INSTAUI_USER_ASSETS_URL_WITH_PREFIX = self.with_prefix(
            self.INSTAUI_USER_ASSETS_URL
        )
        self.INSTAUI_USER_ICONS_URL = (
            f"{self.INSTAUI_USER_ASSETS_URL}/{USER_ASSETS_ICONS_DIR_NAME}"
        )
        self.INSTAUI_USER_ICONS_URL_WITH_PREFIX = self.with_prefix(
            self.INSTAUI_USER_ICONS_URL
        )
        self.STATIC_DIR = STATIC_DIR

        # static files
        self.VUE_JS_HASH_LINK = self._build_static_url(VUE_ES_JS_PATH)
        self.INSTAUI_JS_HASH_LINK = self._build_static_url(APP_ES_JS_PATH)
        self.APP_CSS_LINK = self._build_static_url(APP_CSS_PATH)
        self.FAVICON_LINK = self._build_static_url(FAVICON_PATH)

        self.ASSETS_URL = f"/_instaui_{_INSTA_VERSION}/resource"
        self.ASSETS_URL_WITH_PREFIX = self.with_prefix(self.ASSETS_URL)
        self.FILE_ROUTER_URL = (
            f"{self.ASSETS_URL}/{{hash_part:path}}/{{file_name:path}}"
        )

        # API
        self.WATCH_URL = f"{RUNTIME_API_PREFIX}/watch/sync"
        self.ASYNC_WATCH_URL = f"{RUNTIME_API_PREFIX}/watch/async"
        self.EVENT_URL = f"{RUNTIME_API_PREFIX}/event/sync"
        self.ASYNC_EVENT_URL = f"{RUNTIME_API_PREFIX}/event/async"
        self.DOWNLOAD_URL = f"{RUNTIME_API_PREFIX}/download"
        self.UPLOAD_URL = f"{RUNTIME_API_PREFIX}/upload_file"

        self.WATCH_URL_WITH_PREFIX = self.with_prefix(self.WATCH_URL)
        self.ASYNC_WATCH_URL_WITH_PREFIX = self.with_prefix(self.ASYNC_WATCH_URL)
        self.EVENT_URL_WITH_PREFIX = self.with_prefix(self.EVENT_URL)
        self.ASYNC_EVENT_URL_WITH_PREFIX = self.with_prefix(self.ASYNC_EVENT_URL)
        self.DOWNLOAD_URL_WITH_PREFIX = self.with_prefix(self.DOWNLOAD_URL)
        self.UPLOAD_URL_WITH_PREFIX = self.with_prefix(self.UPLOAD_URL)

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        if not prefix or prefix == "/":
            return ""
        return "/" + prefix.strip("/")

    def with_prefix(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.prefix}{path}"

    def _build_static_url(self, target_path: Path) -> str:
        return f"{self.INSTAUI_STATIC_URL}/{target_path.relative_to(self.STATIC_DIR)}"
