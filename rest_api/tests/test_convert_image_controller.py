"""Tests for the batched local image-conversion API."""

import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.test import SimpleTestCase, override_settings
from PIL import Image

from rest_api.controllers.convert_image_controller import read_source_bytes


def make_source_png(size=(640, 480)) -> bytes:
    """Return a transparent PNG for conversion tests."""
    output = BytesIO()
    Image.new("RGBA", size, (255, 0, 0, 128)).save(output, format="PNG")
    return output.getvalue()


class ConvertImageControllerTests(SimpleTestCase):
    def test_converts_three_outputs_after_reading_original_once(self):
        with TemporaryDirectory() as temporary_directory:
            base_dir = Path(temporary_directory)
            image_id = uuid4()
            png_id = uuid4()
            jpg_id = uuid4()
            thumb_id = uuid4()
            original_path = (
                base_dir
                / "userdata"
                / "uploads"
                / "original"
                / str(image_id)
            )
            original_path.parent.mkdir(parents=True)
            original_path.write_bytes(make_source_png())

            original_url = (
                f"http://testserver/api/userdata/uploads/original/{image_id}"
            )
            outputs = [
                {
                    "uploadId": str(png_id),
                    "outputUrl": (
                        f"http://testserver/api/userdata/uploads/png/{png_id}.png"
                    ),
                    "ext": "png",
                    "size": None,
                },
                {
                    "uploadId": str(jpg_id),
                    "outputUrl": (
                        f"http://testserver/api/userdata/uploads/jpg/{jpg_id}.jpg"
                    ),
                    "ext": "jpg",
                    "size": None,
                },
                {
                    "uploadId": str(thumb_id),
                    "outputUrl": (
                        "http://testserver/api/userdata/uploads/thumbs320x320/"
                        f"{thumb_id}.jpg"
                    ),
                    "ext": "jpg",
                    "size": {"width": 320, "height": 320},
                },
            ]

            with override_settings(BASE_DIR=base_dir), patch(
                "rest_api.controllers.convert_image_controller.read_source_bytes",
                wraps=read_source_bytes,
            ) as read_source:
                response = self.client.post(
                    "/api/projects/data/convert-image",
                    data=json.dumps(
                        {
                            "originalUrl": original_url,
                            "outputs": outputs,
                        }
                    ),
                    content_type="application/json",
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()["outputs"]), 3)
            read_source.assert_called_once_with(original_url)

            with Image.open(
                base_dir / "userdata" / "uploads" / "png" / f"{png_id}.png"
            ) as png_image:
                self.assertEqual(png_image.size, (640, 480))
                self.assertEqual(png_image.format, "PNG")

            with Image.open(
                base_dir / "userdata" / "uploads" / "jpg" / f"{jpg_id}.jpg"
            ) as jpg_image:
                self.assertEqual(jpg_image.size, (640, 480))
                self.assertEqual(jpg_image.mode, "RGB")

            with Image.open(
                base_dir
                / "userdata"
                / "uploads"
                / "thumbs320x320"
                / f"{thumb_id}.jpg"
            ) as thumb_image:
                self.assertEqual(thumb_image.size, (320, 240))
                self.assertEqual(thumb_image.format, "JPEG")

    def test_rejects_an_empty_output_batch(self):
        response = self.client.post(
            "/api/projects/data/convert-image",
            data=json.dumps(
                {
                    "originalUrl": (
                        "http://testserver/api/userdata/uploads/original/image"
                    ),
                    "outputs": [],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
