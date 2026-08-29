"""Tests for selecting and invoking image-conversion implementations."""

import io
import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from rest_api.objects.image_conversion_handler_factory import (
    get_image_conversion_handler,
)
from rest_api.objects.lambda_image_conversion_handler import (
    LambdaImageConversionHandler,
)
from rest_api.objects.local_image_conversion_handler import (
    LocalImageConversionHandler,
)
from rest_api.interfaces.i_image_conversion_handler import IImageConversionHandler


class FakeLambdaClient:
    def __init__(self):
        self.invoke_arguments = None

    def invoke(self, **kwargs):
        self.invoke_arguments = kwargs
        return {
            "Payload": io.BytesIO(
                json.dumps(
                    {
                        "imageId": "image-id",
                        "outputs": [{"uploadId": "upload-id"}],
                    }
                ).encode("utf-8")
            )
        }


class ImageConversionHandlerTests(SimpleTestCase):
    @override_settings(IMAGE_CONVERSION_BACKEND="local")
    def test_factory_returns_local_interface_implementation(self):
        handler = get_image_conversion_handler()

        self.assertIsInstance(handler, LocalImageConversionHandler)
        self.assertIsInstance(handler, IImageConversionHandler)

    @patch(
        "rest_api.objects.local_image_conversion_handler.requests.post"
    )
    def test_local_handler_posts_the_common_batch_payload(self, post):
        response = Mock()
        response.json.return_value = {
            "outputs": [{"uploadId": "upload-id"}],
        }
        post.return_value = response
        handler = LocalImageConversionHandler(
            "http://localhost:8000/api/projects/data/convert-image"
        )
        outputs = [
            {
                "upload_id": "upload-id",
                "output_url": (
                    "http://localhost:8000/api/userdata/uploads/image.png"
                ),
                "ext": "png",
                "size": None,
            }
        ]

        result = handler.convert(
            "http://localhost:8000/api/userdata/uploads/original/image-id",
            outputs,
        )

        response.raise_for_status.assert_called_once_with()
        post.assert_called_once_with(
            "http://localhost:8000/api/projects/data/convert-image",
            json={
                "originalUrl": (
                    "http://localhost:8000/api/userdata/uploads/original/image-id"
                ),
                "outputs": [
                    {
                        "uploadId": "upload-id",
                        "outputUrl": (
                            "http://localhost:8000/api/userdata/uploads/image.png"
                        ),
                        "ext": "png",
                        "size": None,
                    }
                ],
            },
            timeout=30,
        )
        self.assertEqual(result["outputs"][0]["uploadId"], "upload-id")

    @override_settings(
        IMAGE_CONVERSION_LAMBDA_FUNCTION_NAME="image-converter",
    )
    def test_lambda_handler_sends_the_common_batch_payload(self):
        lambda_client = FakeLambdaClient()
        handler = LambdaImageConversionHandler(lambda_client=lambda_client)
        outputs = [
            {
                "upload_id": "upload-id",
                "output_url": "https://example.com/image.png",
                "ext": "png",
                "size": None,
            }
        ]

        result = handler.convert("https://example.com/original", outputs)

        self.assertEqual(result["outputs"][0]["uploadId"], "upload-id")
        self.assertEqual(
            lambda_client.invoke_arguments["FunctionName"],
            "image-converter",
        )
        payload = json.loads(
            lambda_client.invoke_arguments["Payload"].decode("utf-8")
        )
        self.assertEqual(payload["originalUrl"], "https://example.com/original")
        self.assertEqual(
            payload["outputs"],
            [
                {
                    "uploadId": "upload-id",
                    "outputUrl": "https://example.com/image.png",
                    "ext": "png",
                    "size": None,
                }
            ],
        )

    @override_settings(IMAGE_CONVERSION_BACKEND="unsupported")
    def test_factory_rejects_unknown_backend(self):
        with self.assertRaisesRegex(ValueError, "Unsupported image conversion backend"):
            get_image_conversion_handler()
