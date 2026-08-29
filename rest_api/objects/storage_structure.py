"""Validation helpers for provider-neutral storage directory paths."""

from collections.abc import Iterator, Sequence
from pathlib import PurePosixPath

from ..interfaces.i_storage_directory_handler import StorageDirectoryStructure


def iter_storage_directory_paths(
    structure: StorageDirectoryStructure,
) -> Iterator[PurePosixPath]:
    """Validate and yield safe relative leaf-directory paths."""
    if isinstance(structure, (str, bytes)) or not isinstance(structure, Sequence):
        raise TypeError("Storage directory structure must be a sequence of paths.")

    for directory_path in structure:
        if (
            not isinstance(directory_path, PurePosixPath)
            or directory_path.is_absolute()
            or not directory_path.parts
            or any(
                part in {".", ".."} or "\\" in part
                for part in directory_path.parts
            )
        ):
            raise ValueError(
                "Storage directories must be safe relative PurePosixPath values."
            )
        yield directory_path
