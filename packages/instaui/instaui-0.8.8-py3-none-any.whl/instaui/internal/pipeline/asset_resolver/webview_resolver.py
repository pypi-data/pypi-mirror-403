from abc import ABC, abstractmethod
from pathlib import Path
from instaui.systems import file_system
from .resolver import AssetResolver


class AssetMaterializer(ABC):
    """
    Responsible for "materializing" source assets to the target location.
    AssetResolver is only responsible for calculating the target_path.
    Whether to create, copy, and how to copy is determined by this protocol.
    """

    @abstractmethod
    def ensure_dir(self, path: Path) -> None:
        """Ensure the directory exists (idempotent)"""
        pass

    @abstractmethod
    def copy_file(self, src: Path, dst: Path) -> None:
        """Copy a single file"""
        pass

    @abstractmethod
    def copy_dir(self, src: Path, dst: Path) -> None:
        """Copy an entire directory"""
        pass


class WebViewAssetResolver(AssetResolver):
    def __init__(
        self,
        assets_dir_path: Path,
        materializer: AssetMaterializer,
    ) -> None:
        self.assets_dir_path = assets_dir_path
        self.materializer = materializer

    def resolve_asset(self, path: Path) -> str:
        hash_part = file_system.generate_hash_name_from_path(path.parent)
        new_folder_path = self.assets_dir_path.joinpath(hash_part)
        new_path = new_folder_path.joinpath(path.name)

        self.materializer.ensure_dir(new_folder_path)

        if path.is_file():
            self.materializer.copy_file(path, new_path)
            return "./" + self._convert_to_relative(new_path)
        else:
            self.materializer.copy_dir(path, new_path)
            return "./" + self._convert_to_relative(new_path) + "/"

    def _convert_to_relative(self, file_path: Path, relative_parent=False):
        return str(
            file_path.relative_to(
                self.assets_dir_path.parent if relative_parent else self.assets_dir_path
            )
        ).replace("\\", "/")
