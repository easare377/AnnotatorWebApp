"""AWS Lambda implementation of the image-conversion interface."""

import json
import os
from typing import Any, Sequence

import boto3
from django.conf import settings

from ..interfaces.i_image_conversion_handler import IImageConversionHandler


class LambdaImageConversionHandler(IImageConversionHandler):
    """Invoke the configured Lambda with the common batch-conversion payload."""

    def __init__(self, lambda_client=None):
        self._lambda_client = lambda_client

    def _get_lambda_client(self):
        if self._lambda_client is None:
            region_name = getattr(
                settings,
                "IMAGE_CONVERSION_LAMBDA_REGION",
                os.getenv("IMAGE_CONVERSION_LAMBDA_REGION", "us-east-2"),
            )
            self._lambda_client = boto3.client(
                "lambda",
                region_name=region_name,
            )
        return self._lambda_client

    def convert(
        self,
        original_url: str,
        outputs: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        function_name = getattr(
            settings,
            "IMAGE_CONVERSION_LAMBDA_FUNCTION_NAME",
            os.getenv("IMAGE_CONVERSION_LAMBDA_FUNCTION_NAME", "convert_image"),
        )
        payload = {
            "originalUrl": original_url,
            "outputs": [
                {
                    "uploadId": output["upload_id"],
                    "outputUrl": output["output_url"],
                    "ext": output["ext"],
                    "size": output.get("size"),
                }
                for output in outputs
            ],
        }
        response = self._get_lambda_client().invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        if response.get("FunctionError"):
            raise RuntimeError(f"Image conversion Lambda failed: {response_payload}")

        if "statusCode" in response_payload:
            status_code = int(response_payload["statusCode"])
            body = response_payload.get("body")
            if isinstance(body, str):
                body = json.loads(body)
            if status_code >= 400:
                raise RuntimeError(f"Image conversion Lambda failed: {body}")
            return body or {}

        if response_payload.get("error"):
            raise RuntimeError(f"Image conversion Lambda failed: {response_payload}")
        return response_payload.get("output", response_payload)
