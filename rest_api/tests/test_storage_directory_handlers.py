"""Tests for storage-directory initialization implementations."""

from importlib import import_module
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from rest_api.apps import RestApiConfig, initialize_storage_directories
from rest_api.interfaces.i_storage_directory_handler import (
    IStorageDirectoryHandler,
)
from rest_api.objects.local_storage_directory_handler import (
    LocalStorageDirectoryHandler,
)
from rest_api.objects.s3_storage_directory_handler import (
    S3StorageDirectoryHandler,
)
from rest_api.objects.storage_directory_handler_factory import (
    get_storage_directory_handler,
)
from rest_api.objects.url_paths import STORAGE_DIRECTORIES


EXPECTED_STORAGE_DIRECTORIES = (
    "userdata",
    "userdata/uploads",
    "userdata/uploads/original",
    "userdata/uploads/png",
    "userdata/uploads/jpg",
    "userdata/uploads/thumbs320x320",
    "userdata/exports",
    "userdata/exports/exported-segmentation",
    "userdata/exports/exported-segmentation/mask",
    "userdata/exports/exported-segmentation/rgb",
    "userdata/exports/exported-segmentation/zip",
    "userdata/exports/exported-vocs",
    "userdata/exports/exported-jsons",
)


class StorageDirectoryHandlerTests(SimpleTestCase):
    def test_storage_directory_tuple_uses_the_userdata_namespace(self):
        self.assertEqual(
            tuple(str(path) for path in STORAGE_DIRECTORIES),
            (
                "userdata/uploads/original",
                "userdata/uploads/png",
                "userdata/uploads/jpg",
                "userdata/uploads/thumbs320x320",
                "userdata/exports/exported-segmentation/mask",
                "userdata/exports/exported-segmentation/rgb",
                "userdata/exports/exported-segmentation/zip",
                "userdata/exports/exported-vocs",
                "userdata/exports/exported-jsons",
            ),
        )

    def test_local_handler_creates_the_application_structure_idempotently(self):
        with TemporaryDirectory() as temporary_directory:
            handler = LocalStorageDirectoryHandler(temporary_directory)

            handler.create_directories(STORAGE_DIRECTORIES)
            handler.create_directories(STORAGE_DIRECTORIES)

            for relative_path in EXPECTED_STORAGE_DIRECTORIES:
                self.assertTrue(
                    (Path(temporary_directory) / relative_path).is_dir(),
                    relative_path,
                )

    def test_local_handler_rejects_parent_directory_traversal(self):
        with TemporaryDirectory() as temporary_directory:
            handler = LocalStorageDirectoryHandler(temporary_directory)

            with self.assertRaisesRegex(ValueError, "safe relative"):
                handler.create_directories((PurePosixPath("../outside"),))

    def test_s3_handler_accepts_virtual_prefixes_without_network_access(self):
        handler = S3StorageDirectoryHandler()

        handler.create_directories(STORAGE_DIRECTORIES)

        self.assertIsInstance(handler, IStorageDirectoryHandler)

    @override_settings(STORAGE_DIRECTORY_BACKEND="local")
    def test_factory_returns_local_handler(self):
        handler = get_storage_directory_handler()

        self.assertIsInstance(handler, LocalStorageDirectoryHandler)
        self.assertIsInstance(handler, IStorageDirectoryHandler)

    @override_settings(STORAGE_DIRECTORY_BACKEND="s3")
    def test_factory_returns_s3_handler(self):
        handler = get_storage_directory_handler()

        self.assertIsInstance(handler, S3StorageDirectoryHandler)
        self.assertIsInstance(handler, IStorageDirectoryHandler)

    @override_settings(STORAGE_DIRECTORY_BACKEND="unsupported")
    def test_factory_rejects_an_unknown_backend(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported storage directory backend",
        ):
            get_storage_directory_handler()

    @patch("rest_api.apps.get_storage_directory_handler")
    def test_initializer_uses_the_handler_interface(self, get_handler):
        handler = Mock(spec=IStorageDirectoryHandler)
        get_handler.return_value = handler

        initialize_storage_directories()

        handler.create_directories.assert_called_once_with(
            STORAGE_DIRECTORIES
        )

    @patch("rest_api.apps.initialize_storage_directories")
    @patch("rest_api.dbhelper.add_annotation_type_if_not_exist")
    def test_app_ready_initializes_storage(
        self,
        add_annotation_type_if_not_exist,
        initialize_directories,
    ):
        config = RestApiConfig("rest_api", import_module("rest_api"))

        config.ready()

        initialize_directories.assert_called_once_with()
        add_annotation_type_if_not_exist.assert_called_once_with()
