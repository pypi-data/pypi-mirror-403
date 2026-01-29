from __future__ import annotations
from typing import Literal, Optional
from instaui.internal.ui.element import Element


class Video(Element):
    def __init__(
        self,
        src: Optional[str] = None,
        *,
        controls: Optional[bool] = None,
        autoplay: Optional[bool] = None,
        loop: Optional[bool] = None,
        muted: Optional[bool] = None,
        playsinline: Optional[bool] = None,
        poster: Optional[str] = None,
        preload: Optional[Literal["auto", "metadata", "none"]] = None,
    ):
        """
        Creates an HTML video element with configurable playback options.

        Args:
            src (Optional[str]): The URL or path to the video file.
                - If a relative path is provided (e.g., "/xxx.mp4"), it will resolve
                to the `assets` directory in the application root.
                - Absolute URLs (e.g., "https://example.com/video.mp4") are also supported.
            controls (Optional[bool]): Whether to display browser-native video controls.
            autoplay (Optional[bool]): Whether the video should start playing automatically.
            loop (Optional[bool]): Whether the video should loop after reaching the end.
            muted (Optional[bool]): Whether the video should be muted by default.
            playsinline (Optional[bool]): Whether the video should play inline on mobile devices.
            poster (Optional[str]): URL to an image shown as a placeholder before playback starts.
            preload (Optional[Literal["auto", "metadata", "none"]]): Hints how much video data should be preloaded.

        Example:
        .. code-block:: python
            from instaui import ui

            # Play a video from the assets directory
            ui.video("/xxx.mp4", controls=True, autoplay=False)

            # Play a remote video with a custom poster image
            ui.video("https://example.com/video.mp4", poster="/thumbnail.jpg", muted=True)
        """
        super().__init__("ui-video")

        self.props(
            {
                "src": src,
                "controls": controls,
                "autoplay": autoplay,
                "loop": loop,
                "muted": muted,
                "playsinline": playsinline,
                "poster": poster,
                "preload": preload,
            }
        )
