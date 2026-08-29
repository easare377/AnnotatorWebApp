"""Local filesystem implementation for segmentation ZIP export storage."""

import shutil
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from urllib.parse import urljoin

from django.conf import settings

from ..interfaces.i_zip_storage_handler import IZipStorageHandler


class LocalZipStorageHandler(IZipStorageHandler):
    """Write export artifacts beneath ``BASE_DIR`` and return local API URLs."""

    def __init__(
        self,
        base_url: str,
        root_directory: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.root_directory = (
            Path(root_directory)
            if root_directory is not None
            else Path(settings.BASE_DIR)
        )

    def write(self, name: str, content: BinaryIO) -> str:
        """Write one artifact locally and return its absolute API URL."""
        relative_path = PurePosixPath(name)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("Export storage paths must be relative.")

        destination = self.root_directory.joinpath(*relative_path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(content, "seek"):
            content.seek(0)
        with destination.open("wb") as destination_file:
            shutil.copyfileobj(content, destination_file)

        return urljoin(self.base_url, relative_path.as_posix())
