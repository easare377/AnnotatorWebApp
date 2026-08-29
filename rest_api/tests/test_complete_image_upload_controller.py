"""Tests for completing a previously uploaded local image."""

import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase, override_settings
from PIL import Image

from rest_api.controllers.convert_image_controller import convert_image_outputs
from rest_api.models import ImageInfo, ImageType, Projects, UploadedImage
from rest_api.objects.enums.image_status import ImageStatus


def make_test_png() -> bytes:
    """Create a small in-memory image for upload-finalization tests."""
    buffer = BytesIO()
    image = Image.new("RGBA", (20, 10), (255, 0, 0, 128))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class DirectImageConversionHandler:
    """Run conversion in-process while testing the completion controller."""

    def convert(self, original_url, outputs):
        return convert_image_outputs(original_url, outputs)


class CompleteImageUploadControllerTests(TestCase):
    def setUp(self):
        handler_patcher = patch(
            "rest_api.controllers.complete_image_upload_controller."
            "LocalImageConversionHandler",
            return_value=DirectImageConversionHandler(),
        )
        handler_patcher.start()
        self.addCleanup(handler_patcher.stop)

    def test_complete_upload_converts_image_and_saves_database_rows(self):
        project = Projects.objects.create(
            project_name="Project",
            description="Local upload test",
        )

        with TemporaryDirectory() as temporary_directory:
            base_dir = Path(temporary_directory)
            pending_image = ImageInfo.objects.create(
                project_id=project,
                original_filename="sample.png",
                image_width=20,
                image_height=10,
                status=ImageStatus.UPLOADED,
            )
            original_directory = base_dir / "userdata" / "uploads" / "original"
            original_directory.mkdir(parents=True)
            (original_directory / str(pending_image.image_id)).write_bytes(
                make_test_png()
            )

            with override_settings(BASE_DIR=base_dir):
                response = self.client.post(
                    "/api/projects/data/complete-image-upload",
                    data=json.dumps({"imageId": str(pending_image.image_id)}),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 200)
                image_id = response.json()

                self.assertEqual(image_id, str(pending_image.image_id))
                self.assertEqual(ImageInfo.objects.count(), 1)
                self.assertEqual(UploadedImage.objects.count(), 3)
                self.assertEqual(
                    ImageInfo.objects.get(image_id=image_id).status,
                    ImageStatus.COMPLETED,
                )

                for image_type in (ImageType.PNG, ImageType.JPG, ImageType.THUMB):
                    stored_image = UploadedImage.objects.get(
                        image_type=image_type.value
                    )
                    directory = (
                        "thumbs320x320"
                        if image_type == ImageType.THUMB
                        else image_type.value.lower()
                    )
                    self.assertIn(
                        f"/api/userdata/uploads/{directory}/",
                        stored_image.image_url,
                    )
                    extension = "png" if image_type == ImageType.PNG else "jpg"
                    self.assertTrue(
                        (
                            base_dir
                            / "userdata"
                            / "uploads"
                            / directory
                            / f"{stored_image.upload_id}.{extension}"
                        ).exists()
                    )

    def test_complete_upload_rejects_missing_original_upload(self):
        project = Projects.objects.create(
            project_name="Project",
            description="Local upload test",
        )

        with TemporaryDirectory() as temporary_directory:
            pending_image = ImageInfo.objects.create(
                project_id=project,
                original_filename="missing.png",
                image_width=20,
                image_height=10,
                status=ImageStatus.PENDING,
            )
            with override_settings(BASE_DIR=Path(temporary_directory)):
                response = self.client.post(
                    "/api/projects/data/complete-image-upload",
                    data=json.dumps({"imageId": str(pending_image.image_id)}),
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            ImageInfo.objects.get(image_id=pending_image.image_id).status,
            ImageStatus.FAILED,
        )

    def test_retry_creates_outputs_after_the_original_becomes_available(self):
        project = Projects.objects.create(
            project_name="Project",
            description="Local upload retry test",
        )

        with TemporaryDirectory() as temporary_directory:
            base_dir = Path(temporary_directory)
            pending_image = ImageInfo.objects.create(
                project_id=project,
                original_filename="retry.png",
                image_width=20,
                image_height=10,
                status=ImageStatus.PENDING,
            )

            with override_settings(BASE_DIR=base_dir):
                failed_response = self.client.post(
                    "/api/projects/data/complete-image-upload",
                    data=json.dumps({"imageId": str(pending_image.image_id)}),
                    content_type="application/json",
                )
                self.assertEqual(failed_response.status_code, 400)
                self.assertFalse(
                    UploadedImage.objects.filter(image_id=pending_image).exists()
                )

                original_path = (
                    base_dir
                    / "userdata"
                    / "uploads"
                    / "original"
                    / str(pending_image.image_id)
                )
                original_path.parent.mkdir(parents=True)
                original_path.write_bytes(make_test_png())

                retry_response = self.client.post(
                    "/api/projects/data/complete-image-upload",
                    data=json.dumps({"imageId": str(pending_image.image_id)}),
                    content_type="application/json",
                )

            self.assertEqual(retry_response.status_code, 200)
            self.assertEqual(retry_response.json(), str(pending_image.image_id))
            self.assertEqual(
                UploadedImage.objects.filter(image_id=pending_image).count(),
                3,
            )
