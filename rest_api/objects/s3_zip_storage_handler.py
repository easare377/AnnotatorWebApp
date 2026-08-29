"""S3 implementation for segmentation ZIP export storage."""

from typing import BinaryIO

from ..interfaces.i_zip_storage_handler import IZipStorageHandler
from ..s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket


class S3ZipStorageHandler(IZipStorageHandler):
    """Write export artifacts to S3 through the existing bucket adapter."""

    def __init__(self, storage=None) -> None:
        self.storage = storage if storage is not None else UFECLAnnotatorBucket()

    def write(self, name: str, content: BinaryIO) -> str:
        """Write one artifact to S3 and return its public URL."""
        return self.storage.save(name, content)
