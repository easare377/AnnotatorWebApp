"""Tests for selecting and invoking polygon-generation handlers."""

import io
import json
import os
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from rest_api.controllers.generate_polygons_controller import (
    get_generate_polygons_handler,
)
from rest_api.interfaces.i_generate_polygons_handler import (
    IGeneratePolygonsHandler,
)
from rest_api.polygon_generation.lambda_generate_polygons_handler import (
    LambdaGeneratePolygonsHandler,
)
from rest_api.polygon_generation.local_generate_polygons_handler import (
    LocalGeneratePolygonsHandler,
)
from rest_api.polygon_generation.runpod_generate_polygons_handler import (
    RunPodGeneratePolygonsHandler,
)


class PayloadObject:
    def __init__(self, value):
        self.value = value


class FakeLambdaClient:
    def __init__(self):
        self.invoke_arguments = None

    def invoke(self, **kwargs):
        self.invoke_arguments = kwargs
        return {
            "Payload": io.BytesIO(
                json.dumps({"output": [{"points": []}]}).encode("utf-8")
            )
        }


class FakeRunPodEndpoint:
    def __init__(self):
        self.input_payload = None
        self.timeout = None

    def run_sync(self, input_payload, timeout):
        self.input_payload = input_payload
        self.timeout = timeout
        return [{"points": []}]


class GeneratePolygonsHandlerTests(SimpleTestCase):
    def test_factory_returns_configured_interface_implementation(self):
        expected_handlers = {
            "local": LocalGeneratePolygonsHandler,
            "lambda": LambdaGeneratePolygonsHandler,
            "runpod": RunPodGeneratePolygonsHandler,
        }

        for backend, expected_handler in expected_handlers.items():
            with self.subTest(backend=backend):
                with patch.dict(os.environ, {"SAM_BACKEND": backend}):
                    handler = get_generate_polygons_handler()

                self.assertIsInstance(handler, expected_handler)
                self.assertIsInstance(handler, IGeneratePolygonsHandler)

    @patch(
        "rest_api.polygon_generation.local_generate_polygons_handler."
        "requests.post"
    )
    def test_local_handler_posts_json_payload(self, post):
        response = Mock()
        response.json.return_value = {"output": [{"points": []}]}
        post.return_value = response
        handler = LocalGeneratePolygonsHandler("http://localhost:8001")

        result = handler.generate(
            {
                "input": {
                    "image_info": {
                        "image_url": (
                            "http://127.0.0.1:8000/"
                            "api/userdata/uploads/jpg/image.jpg"
                        )
                    },
                    "model_config": PayloadObject("config"),
                }
            }
        )

        post.assert_called_once_with(
            "http://localhost:8001/run",
            json={
                "input": {
                    "image_info": {
                        "image_url": (
                            "http://host.docker.internal:8000/"
                            "api/userdata/uploads/jpg/image.jpg"
                        )
                    },
                    "model_config": {"value": "config"},
                }
            },
            timeout=120,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(result, [{"points": []}])

    @patch(
        "rest_api.polygon_generation.local_generate_polygons_handler."
        "requests.post"
    )
    def test_local_handler_preserves_remote_image_url(self, post):
        response = Mock()
        response.json.return_value = {"output": []}
        post.return_value = response
        handler = LocalGeneratePolygonsHandler("http://localhost:8001/run")
        image_url = "https://example.com/image.jpg?signature=value"

        handler.generate(
            {"input": {"image_info": {"image_url": image_url}}}
        )

        self.assertEqual(
            post.call_args.kwargs["json"]["input"]["image_info"]["image_url"],
            image_url,
        )

    @patch.dict(
        os.environ,
        {
            "SAM_LAMBDA_FUNCTION_NAME": "sam-function",
        },
    )
    def test_lambda_handler_invokes_function(self):
        lambda_client = FakeLambdaClient()
        handler = LambdaGeneratePolygonsHandler(lambda_client=lambda_client)

        result = handler.generate(
            {"input": {"model_config": PayloadObject("config")}}
        )

        self.assertEqual(result, [{"points": []}])
        self.assertEqual(
            lambda_client.invoke_arguments["FunctionName"],
            "sam-function",
        )
        payload = json.loads(
            lambda_client.invoke_arguments["Payload"].decode("utf-8")
        )
        self.assertEqual(
            payload,
            {"input": {"model_config": {"value": "config"}}},
        )

    def test_runpod_handler_submits_payload(self):
        endpoint = FakeRunPodEndpoint()
        handler = RunPodGeneratePolygonsHandler(endpoint=endpoint)
        input_payload = {"input": {"image_info": {"image_url": "url"}}}

        result = handler.generate(input_payload)

        self.assertEqual(result, [{"points": []}])
        self.assertEqual(endpoint.input_payload, input_payload)
        self.assertEqual(endpoint.timeout, 120)

    @patch.dict(os.environ, {"SAM_BACKEND": "unsupported"})
    def test_factory_rejects_unsupported_backend(self):
        with self.assertRaisesRegex(ValueError, "Unsupported SAM backend"):
            get_generate_polygons_handler()
