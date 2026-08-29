"""Contract for initializing storage directory paths."""

from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import Protocol, TypeAlias, runtime_checkable


StorageDirectoryStructure: TypeAlias = Sequence[PurePosixPath]


@runtime_checkable
class IStorageDirectoryHandler(Protocol):
    """Initialize the stable directory prefixes required by a storage backend."""

    def create_directories(
        self,
        structure: StorageDirectoryStructure,
    ) -> None:
        """Create or initialize every leaf directory in ``structure``."""
        ...
