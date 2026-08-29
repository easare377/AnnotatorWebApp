"""Tests for segmentation ZIP export storage backends."""

import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from django.test import RequestFactory, SimpleTestCase

from rest_api.controllers.export_segmentation_mask_data_controller import (
    ExportDataController,
)
from rest_api.interfaces.i_zip_storage_handler import IZipStorageHandler
from rest_api.objects.local_zip_storage_handler import LocalZipStorageHandler
from rest_api.objects.s3_zip_storage_handler import S3ZipStorageHandler


class ZipStorageHandlerTests(SimpleTestCase):
    def test_local_handler_writes_artifact_and_returns_api_url(self):
        with TemporaryDirectory() as temporary_directory:
            handler = LocalZipStorageHandler(
                "http://testserver/api/",
                Path(temporary_directory),
            )

            url = handler.write(
                "userdata/exports/exported-segmentation/mask/export/mask.png",
                io.BytesIO(b"mask-data"),
            )

            self.assertIsInstance(handler, IZipStorageHandler)
            self.assertEqual(
                url,
                "http://testserver/api/userdata/exports/exported-segmentation/"
                "mask/export/mask.png",
            )
            self.assertEqual(
                (
                    Path(temporary_directory)
                    / "userdata/exports/exported-segmentation/mask/export/mask.png"
                ).read_bytes(),
                b"mask-data",
            )

    def test_s3_handler_delegates_writes_to_bucket_storage(self):
        storage = Mock()
        storage.save.return_value = "https://bucket.example/mask.png"
        handler = S3ZipStorageHandler(storage)
        content = io.BytesIO(b"mask-data")

        url = handler.write("userdata/mask.png", content)

        self.assertIsInstance(handler, IZipStorageHandler)
        self.assertEqual(url, "https://bucket.example/mask.png")
        storage.save.assert_called_once_with("userdata/mask.png", content)

    def test_controller_selects_the_local_zip_storage_handler(self):
        controller = ExportDataController()
        controller.request = RequestFactory().post("/api/projects/data/export")

        handler = controller.get_zip_storage_handler()

        self.assertIsInstance(handler, LocalZipStorageHandler)
        self.assertEqual(handler.base_url, "http://testserver/api/")
