"""Local HTTP implementation of the polygon-generation interface."""

import os
from typing import Any, Sequence
from urllib.parse import urlsplit, urlunsplit

import requests

from ..interfaces.i_generate_polygons_handler import IGeneratePolygonsHandler
from .payload import convert_to_jsonable


LOCAL_SAM_REQUEST_TIMEOUT_SECONDS = 120
LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}
DOCKER_HOSTNAME = "host.docker.internal"


def docker_accessible_url(url: str) -> str:
    """Replace a local URL hostname with Docker's host gateway hostname."""
    parsed_url = urlsplit(url)
    if parsed_url.hostname not in LOCAL_HOSTNAMES:
        return url

    port = f":{parsed_url.port}" if parsed_url.port is not None else ""
    return urlunsplit(
        parsed_url._replace(netloc=f"{DOCKER_HOSTNAME}{port}")
    )


def prepare_local_worker_payload(
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    """Return a JSON payload whose local image URL is reachable from Docker."""
    payload = convert_to_jsonable(input_payload)
    image_info = payload.get("input", {}).get("image_info", {})
    image_url = image_info.get("image_url")
    if image_url:
        image_info["image_url"] = docker_accessible_url(str(image_url))
    return payload


class LocalGeneratePolygonsHandler(IGeneratePolygonsHandler):
    """Send polygon-generation jobs to the local SAM worker."""

    def __init__(self, worker_url: str | None = None) -> None:
        self.worker_url = worker_url or os.getenv(
            "SAM_WORKER_LOCAL_URL",
            "http://localhost:8001/run",
        )
        if not self.worker_url.endswith("/run"):
            self.worker_url = f"{self.worker_url.rstrip('/')}/run"

    def generate(
        self,
        input_payload: dict[str, Any],
    ) -> Sequence[Any]:
        response = requests.post(
            self.worker_url,
            json=prepare_local_worker_payload(input_payload),
            timeout=LOCAL_SAM_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        worker_output = response.json()
        return worker_output.get("output", worker_output)
