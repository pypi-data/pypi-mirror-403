from __future__ import annotations
from typing import TYPE_CHECKING, Generator


if TYPE_CHECKING:
    from instaui.internal.ui.layout import Layout


class LayoutContext:
    def __init__(self, layouts: list[Layout]) -> None:
        self._layouts = sorted(
            layouts,
            key=lambda v: v.priority,
            reverse=True,
        )
        self._gens: list[Generator[None, None, None]] = []

    def __enter__(self):
        for layout in self._layouts:
            gen = layout.create_generator()
            try:
                next(gen)
            except StopIteration:
                raise RuntimeError("@ui.layout must yield exactly once")
            self._gens.append(gen)

        return self

    def __exit__(self, *_):
        for gen in reversed(self._gens):
            try:
                next(gen)
            except StopIteration:
                continue
            else:
                raise RuntimeError("@ui.layout must yield exactly once")

        self._gens.clear()
        return False
