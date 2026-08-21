"""Tests for removing images and their stored files."""

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

from django.test import SimpleTestCase

from rest_api.controllers.remove_images_controller import (
    RemoveImagesController,
    normalize_image_ids,
    remove_images,
    storage_key_from_url,
)
from rest_api.objects.remove_images_request import RemoveImagesRequest


class RemoveImagesControllerTests(SimpleTestCase):
    def test_endpoint_accepts_camel_case_image_ids(self):
        response = self.client.post(
            "/api/projects/data/remove-images",
            data={"imageIds": []},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_normalize_image_ids_deduplicates_ids(self):
        image_id = "8ee7e247-f5cf-4df1-ab02-fc24ce9ca82b"

        normalized_ids = normalize_image_ids([image_id, image_id])

        self.assertEqual(normalized_ids, [UUID(image_id)])

    def test_storage_key_from_virtual_hosted_s3_url(self):
        key = storage_key_from_url(
            "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/images/png/example.png",
            "uf-ecl-annotator-bucket",
        )

        self.assertEqual(key, "images/png/example.png")

    def test_storage_key_rejects_another_bucket(self):
        with self.assertRaises(ValueError):
            storage_key_from_url(
                "https://another-bucket.s3.amazonaws.com/images/example.png",
                "uf-ecl-annotator-bucket",
            )

    @patch("rest_api.controllers.remove_images_controller.transaction.atomic")
    @patch("rest_api.controllers.remove_images_controller.UFECLAnnotatorBucket")
    @patch("rest_api.controllers.remove_images_controller.UploadedImage")
    @patch("rest_api.controllers.remove_images_controller.ImageInfo")
    def test_remove_images_deletes_files_before_database_rows(
        self,
        image_info_model,
        uploaded_image_model,
        storage_class,
        atomic,
    ):
        image_id = UUID("8ee7e247-f5cf-4df1-ab02-fc24ce9ca82b")
        image_queryset = MagicMock()
        image_queryset.__iter__.return_value = iter(
            [SimpleNamespace(image_id=image_id)]
        )
        image_info_model.objects.select_for_update.return_value.filter.return_value = (
            image_queryset
        )
        uploaded_image_model.objects.filter.return_value.values_list.return_value = [
            "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/images/png/example.png",
            "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/images/jpeg/example.jpg",
            "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/images/thumbs/example_320.jpg",
        ]
        storage = storage_class.return_value
        storage.bucket_name = "uf-ecl-annotator-bucket"
        atomic.return_value = nullcontext()

        deleted_ids = remove_images([str(image_id)])

        self.assertEqual(deleted_ids, [str(image_id)])
        self.assertEqual(
            [call.args[0] for call in storage.delete.call_args_list],
            [
                "images/png/example.png",
                "images/jpeg/example.jpg",
                "images/thumbs/example_320.jpg",
            ],
        )
        image_queryset.delete.assert_called_once_with()

    @patch("rest_api.controllers.remove_images_controller.transaction.atomic")
    @patch("rest_api.controllers.remove_images_controller.UFECLAnnotatorBucket")
    @patch("rest_api.controllers.remove_images_controller.UploadedImage")
    @patch("rest_api.controllers.remove_images_controller.ImageInfo")
    def test_storage_failure_preserves_database_rows(
        self,
        image_info_model,
        uploaded_image_model,
        storage_class,
        atomic,
    ):
        image_id = UUID("8ee7e247-f5cf-4df1-ab02-fc24ce9ca82b")
        image_queryset = MagicMock()
        image_queryset.__iter__.return_value = iter(
            [SimpleNamespace(image_id=image_id)]
        )
        image_info_model.objects.select_for_update.return_value.filter.return_value = (
            image_queryset
        )
        uploaded_image_model.objects.filter.return_value.values_list.return_value = [
            "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/images/png/example.png"
        ]
        storage = storage_class.return_value
        storage.bucket_name = "uf-ecl-annotator-bucket"
        storage.delete.side_effect = RuntimeError("S3 unavailable")
        atomic.return_value = nullcontext()

        with self.assertRaises(RuntimeError):
            remove_images([str(image_id)])

        image_queryset.delete.assert_not_called()

    @patch("rest_api.controllers.remove_images_controller.remove_images")
    def test_controller_returns_deleted_ids(self, remove_images_mock):
        image_id = "8ee7e247-f5cf-4df1-ab02-fc24ce9ca82b"
        remove_images_mock.return_value = [image_id]

        response = RemoveImagesController().process_post_request(
            RemoveImagesRequest(image_ids=[image_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.body,
            {"deletedImageIds": [image_id], "deletedCount": 1},
        )
