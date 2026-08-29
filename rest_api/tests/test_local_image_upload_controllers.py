"""Tests for local image upload controllers."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from uuid import UUID

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from rest_api.models import ImageInfo, Projects
from rest_api.objects.enums.image_status import ImageStatus


class LocalImageUploadControllerTests(TestCase):
    def test_generates_signed_upload_links_and_stores_an_uploaded_image(self):
        project = Projects.objects.create(
            project_name="Project",
            description="Local upload test",
        )

        with TemporaryDirectory() as temporary_directory:
            with override_settings(BASE_DIR=Path(temporary_directory)):
                link_response = self.client.post(
                    "/api/projects/data/generate-upload-image-link",
                    data=json.dumps(
                        {
                            "projectId": str(project.project_id),
                            "images": [
                                {
                                    "imageDetails": {
                                        "fileName": "image.png",
                                        "width": 20,
                                        "height": 10,
                                    }
                                }
                            ],
                        }
                    ),
                    content_type="application/json",
                )

                self.assertEqual(link_response.status_code, 200)
                upload = link_response.json()["uploads"][0]
                image_id = UUID(upload["imageId"])
                upload_link = upload["uploadLink"]
                upload_url = urlparse(upload_link["uploadUrl"])
                self.assertEqual(upload_link["imageId"], str(image_id))
                self.assertEqual(upload_link["method"], "POST")

                upload_response = self.client.post(
                    f"{upload_url.path}?{upload_url.query}",
                    data={
                        "image": SimpleUploadedFile(
                            "image.png",
                            b"local image bytes",
                            content_type="image/png",
                        )
                    },
                )

                self.assertEqual(upload_response.status_code, 200)
                self.assertEqual(upload_response.json()["imageId"], str(image_id))
                self.assertEqual(
                    upload_response.json()["storageKey"],
                    f"userdata/uploads/original/{image_id}",
                )
                self.assertEqual(
                    (
                        Path(temporary_directory)
                        / "userdata"
                        / "uploads"
                        / "original"
                        / str(image_id)
                    ).read_bytes(),
                    b"local image bytes",
                )
                self.assertEqual(
                    ImageInfo.objects.get(image_id=image_id).status,
                    ImageStatus.UPLOADED,
                )

    def test_rejects_upload_without_a_signed_link(self):
        response = self.client.post(
            "/api/projects/data/upload-image/6d7c9c1d-31fa-43a5-88ab-8e90980c5a1b",
            data={
                "image": SimpleUploadedFile(
                    "image.png",
                    b"local image bytes",
                    content_type="image/png",
                )
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_rejects_invalid_upload_count(self):
        project = Projects.objects.create(
            project_name="Project",
            description="Local upload test",
        )
        response = self.client.post(
            "/api/projects/data/generate-upload-image-link",
            data=json.dumps(
                {
                    "projectId": str(project.project_id),
                    "images": [],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
