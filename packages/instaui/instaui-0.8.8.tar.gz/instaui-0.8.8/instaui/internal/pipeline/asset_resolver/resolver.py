from abc import abstractmethod, ABC
from pathlib import Path


class AssetResolver(ABC):
    @abstractmethod
    def resolve_asset(self, path: Path) -> str:
        pass
