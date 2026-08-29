"""AWS Lambda implementation of the polygon-generation interface."""

import json
import os
from typing import Any, Sequence

import boto3

from ..interfaces.i_generate_polygons_handler import IGeneratePolygonsHandler
from .payload import convert_to_jsonable


class LambdaGeneratePolygonsHandler(IGeneratePolygonsHandler):
    """Invoke the configured SAM Lambda function."""

    def __init__(self, lambda_client=None) -> None:
        self._lambda_client = lambda_client

    def _get_lambda_client(self):
        if self._lambda_client is None:
            self._lambda_client = boto3.client(
                "lambda",
                region_name=os.getenv("SAM_LAMBDA_REGION", "us-east-2"),
            )
        return self._lambda_client

    def generate(
        self,
        input_payload: dict[str, Any],
    ) -> Sequence[Any]:
        response = self._get_lambda_client().invoke(
            FunctionName=os.getenv(
                "SAM_LAMBDA_FUNCTION_NAME",
                "sam_inference",
            ),
            InvocationType="RequestResponse",
            Payload=json.dumps(
                convert_to_jsonable(input_payload)
            ).encode("utf-8"),
        )

        lambda_payload = json.loads(
            response["Payload"].read().decode("utf-8")
        )
        if response.get("FunctionError"):
            raise RuntimeError(lambda_payload)
        if lambda_payload.get("error"):
            raise RuntimeError(lambda_payload)

        return lambda_payload.get("output", lambda_payload)
