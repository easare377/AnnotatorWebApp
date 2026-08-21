"""Resolve the configured image-conversion backend."""

import os

from django.conf import settings

from ..interfaces.i_image_conversion_handler import IImageConversionHandler
from .lambda_image_conversion_handler import LambdaImageConversionHandler
from .local_image_conversion_handler import LocalImageConversionHandler


def get_image_conversion_handler() -> IImageConversionHandler:
    """Return the local or Lambda conversion handler selected by configuration."""
    backend = getattr(
        settings,
        "IMAGE_CONVERSION_BACKEND",
        os.getenv("IMAGE_CONVERSION_BACKEND", "local"),
    ).lower()

    if backend == "local":
        return LocalImageConversionHandler()
    if backend == "lambda":
        return LambdaImageConversionHandler()
    raise ValueError(f"Unsupported image conversion backend: {backend}")
