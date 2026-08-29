"""Local implementation of the image-conversion interface."""

from typing import Any, Sequence

import requests

from ..interfaces.i_image_conversion_handler import IImageConversionHandler


DEFAULT_LOCAL_CONVERSION_URL = (
    "http://localhost:8000/api/projects/data/convert-image"
)
LOCAL_CONVERSION_REQUEST_TIMEOUT_SECONDS = 30


class LocalImageConversionHandler(IImageConversionHandler):
    """Request image conversion through the local Django API."""

    def __init__(
        self,
        conversion_url: str = DEFAULT_LOCAL_CONVERSION_URL,
    ) -> None:
        self.conversion_url = conversion_url

    def convert(
        self,
        original_url: str,
        outputs: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        response = requests.post(
            self.conversion_url,
            json={
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
            },
            timeout=LOCAL_CONVERSION_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
