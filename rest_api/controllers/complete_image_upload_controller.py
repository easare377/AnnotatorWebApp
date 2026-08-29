"""Finalize an original upload by creating its three converted images."""

from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid4

from django.db import transaction

from rest_api import dbhelper as dbh

from ..controller import Controller, ok
from ..decorators.route import route
from ..objects.local_image_conversion_handler import (
    LocalImageConversionHandler,
)
from ..interfaces.i_image_conversion_handler import IImageConversionHandler
from ..models import ImageInfo, ImageType, UploadedImage
from ..objects.enums.image_status import ImageStatus
from ..objects.url_paths import (
    JPG_UPLOADS_PATH,
    ORIGINAL_UPLOADS_PATH,
    PNG_UPLOADS_PATH,
    THUMBS320X320_UPLOADS_PATH,
)


OUTPUT_DETAILS = {
    ImageType.PNG: {"path": PNG_UPLOADS_PATH, "ext": "png", "size": None},
    ImageType.JPG: {"path": JPG_UPLOADS_PATH, "ext": "jpg", "size": None},
    ImageType.THUMB: {
        "path": THUMBS320X320_UPLOADS_PATH,
        "ext": "jpg",
        "size": {"width": 320, "height": 320},
    },
}


def get_image_info(image_id: UUID) -> ImageInfo:
    """Return the image record created when its upload URL was generated."""
    try:
        return ImageInfo.objects.get(image_id=image_id)
    except ImageInfo.DoesNotExist:
        raise ValueError(f"Image with ID {image_id} does not exist.")


def get_original_image_url(request, image_id: UUID) -> str:
    """Return the URL of the locally uploaded original image."""
    return request.build_absolute_uri(f"/api/{ORIGINAL_UPLOADS_PATH}/{image_id}")


def converted_image_url(
    request,
    upload_id: UUID,
    image_type: ImageType,
) -> str:
    """Generate the destination URL for a converted local image."""
    output_details = OUTPUT_DETAILS[image_type]
    return request.build_absolute_uri(
        f"/api/{output_details['path']}/"
        f"{upload_id}.{output_details['ext']}"
    )


def get_image_output_details(upload_id, output_url, size=None) -> dict:
    """Return one conversion target using the extension from its URL."""
    extension = Path(urlparse(output_url).path).suffix.lstrip(".").lower()
    return {
        "upload_id": str(upload_id),
        "output_url": output_url,
        "ext": extension,
        "size": (
            {"width": size[0], "height": size[1]}
            if size is not None
            else None
        ),
    }


def mark_image_completed(image_id: UUID) -> None:
    """Mark the image completed after the complete output batch succeeds."""
    with transaction.atomic():
        ImageInfo.objects.select_for_update().get(image_id=image_id)
        dbh.update_image_info_status(
            image_id,
            ImageStatus.COMPLETED,
        )


@route("projects/data/complete-image-upload")
class CompleteImageUploadController(Controller):
    """Generate local conversion jobs for one previously uploaded image."""

    def get_conversion_handler(self) -> IImageConversionHandler:
        """Return the local image-conversion implementation."""
        conversion_url = self.request.build_absolute_uri(
            "/api/projects/data/convert-image"
        )
        return LocalImageConversionHandler(conversion_url)

    def process_post_request(self, request_object):
        image_id = UUID(str(request_object.image_id))
        image_info = get_image_info(image_id)

        if (
            image_info.status == ImageStatus.COMPLETED
            and UploadedImage.objects.filter(image_id=image_info).count() == 3
        ):
            return ok(image_id)

        png_id = uuid4()
        jpg_id = uuid4()
        thumb_id = uuid4()
        png_url = converted_image_url(self.request, png_id, ImageType.PNG)
        jpg_url = converted_image_url(self.request, jpg_id, ImageType.JPG)
        thumb_url = converted_image_url(self.request, thumb_id, ImageType.THUMB)
        conversion_outputs = []
        conversion_outputs.append(get_image_output_details(png_id, png_url))
        conversion_outputs.append(get_image_output_details(jpg_id, jpg_url))
        conversion_outputs.append(
            get_image_output_details(thumb_id, thumb_url, (320, 320))
        )
        original_image_url = get_original_image_url(self.request, image_id)

        try:
            conversion_handler = self.get_conversion_handler()
            conversion_handler.convert(
                original_image_url,
                conversion_outputs,
            )
            dbh.save_upload_info(image_id, png_id, png_url, ImageType.PNG)
            dbh.save_upload_info(image_id, jpg_id, jpg_url, ImageType.JPG)
            dbh.save_upload_info(image_id, thumb_id, thumb_url, ImageType.THUMB)
            mark_image_completed(image_id)
        except Exception:
            dbh.update_image_info_status(image_id, ImageStatus.FAILED)
            raise

        return ok(image_id)
