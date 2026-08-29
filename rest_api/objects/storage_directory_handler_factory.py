"""Resolve the configured storage-directory implementation."""

import os

from django.conf import settings

from ..interfaces.i_storage_directory_handler import IStorageDirectoryHandler
from .local_storage_directory_handler import LocalStorageDirectoryHandler
from .s3_storage_directory_handler import S3StorageDirectoryHandler


def get_storage_directory_handler() -> IStorageDirectoryHandler:
    """Return the configured local or S3 directory handler."""
    backend = getattr(
        settings,
        "STORAGE_DIRECTORY_BACKEND",
        os.getenv("STORAGE_DIRECTORY_BACKEND", "local"),
    ).lower()

    if backend == "local":
        return LocalStorageDirectoryHandler()
    if backend == "s3":
        return S3StorageDirectoryHandler()
    raise ValueError(f"Unsupported storage directory backend: {backend}")
