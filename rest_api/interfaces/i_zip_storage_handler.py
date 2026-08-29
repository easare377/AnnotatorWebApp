"""Contract for storage used while creating segmentation ZIP exports."""

from typing import BinaryIO, Protocol, runtime_checkable


@runtime_checkable
class IZipStorageHandler(Protocol):
    """Persist an export artifact and return a URL that can retrieve it."""

    def write(self, name: str, content: BinaryIO) -> str:
        """Write ``content`` below ``name`` and return its public URL."""
        ...
