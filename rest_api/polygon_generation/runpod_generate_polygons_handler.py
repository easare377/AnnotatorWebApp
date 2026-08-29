"""RunPod implementation of the polygon-generation interface."""

from typing import Any, Sequence

import runpod

from ..interfaces.i_generate_polygons_handler import IGeneratePolygonsHandler


RUNPOD_API_KEY = "5AKXD6UDVL773K7OGNG7OSEOUPZWX3BLM57XNM33"
RUNPOD_ENDPOINT_ID = "adoqht5dtckgr7"
RUNPOD_REQUEST_TIMEOUT_SECONDS = 120


class RunPodGeneratePolygonsHandler(IGeneratePolygonsHandler):
    """Submit polygon-generation jobs to the configured RunPod endpoint."""

    def __init__(self, endpoint=None) -> None:
        self._endpoint = endpoint

    def generate(
        self,
        input_payload: dict[str, Any],
    ) -> Sequence[Any]:
        runpod.api_key = RUNPOD_API_KEY
        endpoint = self._endpoint or runpod.Endpoint(RUNPOD_ENDPOINT_ID)
        return endpoint.run_sync(
            input_payload,
            timeout=RUNPOD_REQUEST_TIMEOUT_SECONDS,
        )
