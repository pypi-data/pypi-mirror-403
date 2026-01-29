from pathlib import Path
from typing import Final


_PROJECT_DIR: Final = Path(__file__).parent
STATIC_DIR: Final = _PROJECT_DIR.joinpath("static")
COMPILED_DIR: Final = STATIC_DIR.joinpath("compiled")

FAVICON_PATH: Final = STATIC_DIR.joinpath("insta-ui.ico")

# compiled files
APP_ES_JS_PATH: Final = COMPILED_DIR.joinpath("insta-ui.esm-browser.prod.js")
APP_ES_JS_MAP_PATH: Final = COMPILED_DIR.joinpath("insta-ui.js.map")
APP_CSS_PATH: Final = COMPILED_DIR.joinpath("insta-ui.css")
VUE_ES_JS_PATH: Final = COMPILED_DIR.joinpath("vue.esm-browser.prod.js")
