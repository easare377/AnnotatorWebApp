"""S3 storage-directory implementation."""

from ..interfaces.i_storage_directory_handler import (
    IStorageDirectoryHandler,
    StorageDirectoryStructure,
)
from .storage_structure import iter_storage_directory_paths


class S3StorageDirectoryHandler(IStorageDirectoryHandler):
    """Initialize S3 prefixes without creating unnecessary marker objects.

    S3 has a flat object-key namespace rather than real directories. Prefixes
    become available as soon as an object is written, so startup only validates
    the requested structure and deliberately performs no network requests.
    """

    def create_directories(
        self,
        structure: StorageDirectoryStructure,
    ) -> None:
        """Validate directory prefixes; S3 creates them on object write."""
        for _ in iter_storage_directory_paths(structure):
            pass
