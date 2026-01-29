from typing import Protocol
from instaui.internal.assets.base import AssetsDeclaration


class AssetsProcessor(Protocol):
    def process(self, assets: AssetsDeclaration) -> None:
        """In-place mutate assets"""
        ...
