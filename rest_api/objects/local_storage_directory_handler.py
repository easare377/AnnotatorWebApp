"""Local filesystem storage-directory implementation."""

from pathlib import Path

from django.conf import settings

from ..interfaces.i_storage_directory_handler import (
    IStorageDirectoryHandler,
    StorageDirectoryStructure,
)
from .storage_structure import iter_storage_directory_paths


class LocalStorageDirectoryHandler(IStorageDirectoryHandler):
    """Create application storage directories below one local root."""

    def __init__(self, root_directory: str | Path | None = None) -> None:
        self.root_directory = Path(
            root_directory if root_directory is not None else settings.BASE_DIR
        )

    def create_directories(
        self,
        structure: StorageDirectoryStructure,
    ) -> None:
        """Create all directories idempotently below the configured root."""
        directory_paths = tuple(iter_storage_directory_paths(structure))
        for directory_path in directory_paths:
            self.root_directory.joinpath(*directory_path.parts).mkdir(
                parents=True,
                exist_ok=True,
            )
