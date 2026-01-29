from __future__ import annotations
from typing import Literal, Optional, Union
from instaui.internal.ui.element import Element


class Image(Element):
    def __init__(
        self,
        src: Optional[str] = None,
        *,
        alt: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
        title: Optional[str] = None,
        srcset: Optional[str] = None,
        sizes: Optional[str] = None,
        loading: Optional[Literal["lazy", "eager"]] = None,
    ):
        """
        Creates an HTML `<img>` element with configurable attributes.

        The `src` parameter specifies the image source. If a relative path is provided
        (starting with `/`), it resolves to files in the application's `assets/` directory.
        Absolute URLs are used directly.

        Args:
            src: Path to the image file or URL. Relative paths must start with `/` and
                 resolve to files in the `assets/` directory. Example: `/xxx.png` refers to
                 `assets/xxx.png`.
            alt: Alternative text for accessibility and SEO when the image cannot be displayed.
            width: Width of the image in pixels or percentage (e.g., `300` or `"100%"`).
            height: Height of the image in pixels or percentage (e.g., `200` or `"50%"`).
            title: Tooltip text displayed when hovering over the image.
            srcset: Comma-separated list of image URLs with descriptors for responsive design.
            sizes: Media query conditions to define image size based on viewport width.
            loading: Specifies whether the image should load lazily (`"lazy"`) or eagerly (`"eager"`).

        Example:
        .. code-block:: python
            # Renders <img src="/xxx.png" alt="Example Image" width="300" height="200">
            html.image("/xxx.png", alt="Example Image", width=300, height=200)
        """
        super().__init__("ui-img")

        self.props(
            {
                "src": src,
                "alt": alt,
                "width": width,
                "height": height,
                "title": title,
                "srcset": srcset,
                "sizes": sizes,
                "loading": loading,
            }
        )
