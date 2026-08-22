"""API controller for deleting selected project images and their stored files.

The endpoint removes every uploaded representation associated with an image
(PNG, JPEG, and thumbnail) from S3 before deleting the image's database row.
Database foreign-key cascades then remove uploaded-image metadata, polygons,
and inner polygons.
"""

from urllib.parse import unquote, urlparse
from uuid import UUID

from django.db import transaction

from ..controller import Controller, ok
from ..decorators.route import route
from ..models import ImageInfo, UploadedImage
from ..objects.remove_images_request import RemoveImagesRequest
from ..s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket


def normalize_image_ids(image_ids: list[str]) -> list[UUID]:
    """Validate image IDs, convert them to UUIDs, and remove duplicates.

    Args:
        image_ids: Image identifiers supplied by the API request.

    Returns:
        UUIDs in their original request order with duplicates removed.

    Raises:
        ValueError: If the input is empty, is not a list, or contains an
            invalid UUID.
    """
    if not isinstance(image_ids, list) or not image_ids:
        raise ValueError("imageIds must be a non-empty list.")

    normalized_ids = []
    seen_ids = set()
    for image_id in image_ids:
        try:
            normalized_id = UUID(str(image_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid image ID: {image_id}") from exc
        if normalized_id not in seen_ids:
            normalized_ids.append(normalized_id)
            seen_ids.add(normalized_id)
    return normalized_ids


def storage_key_from_url(image_url: str, bucket_name: str) -> str:
    """Extract an S3 object key from a URL owned by the upload bucket.

    Both virtual-hosted URLs (``bucket.s3.amazonaws.com/key``) and path-style
    URLs (``s3.amazonaws.com/bucket/key``) are supported. URLs belonging to a
    different bucket are rejected to prevent deletion outside the configured
    upload storage.

    Args:
        image_url: Absolute URL stored in an ``UploadedImage`` record.
        bucket_name: Name of the configured S3 bucket.

    Returns:
        The decoded S3 object key.

    Raises:
        ValueError: If the URL is empty or does not reference the bucket.
    """
    parsed_url = urlparse(image_url)
    hostname = (parsed_url.hostname or "").lower()
    key = unquote(parsed_url.path).lstrip("/")
    bucket_name = bucket_name.lower()

    if hostname == bucket_name or hostname.startswith(f"{bucket_name}."):
        if key:
            return key
    else:
        path_prefix = f"{bucket_name}/"
        if key.lower().startswith(path_prefix):
            return key[len(path_prefix):]

    raise ValueError(
        f"Image URL does not belong to the configured upload bucket: {image_url}"
    )


def remove_images(image_ids: list[str]) -> list[str]:
    """Delete selected images, their S3 files, and related database records.

    All requested images must exist. Their database rows are locked while the
    operation runs, and S3 files are deleted before the rows are removed. If a
    storage deletion fails, the database transaction rolls back so the stored
    URLs remain available for a later retry.

    Deleting ``ImageInfo`` rows cascades to ``UploadedImage``, ``Polygons``,
    and ``InnerPolygons`` records through their foreign keys.

    Args:
        image_ids: Image UUID strings from the request.

    Returns:
        Canonical UUID strings for the deleted images.

    Raises:
        ValueError: If an ID is invalid, an image does not exist, or a stored
            URL does not belong to the configured bucket.
        Exception: Propagates storage and database errors to the base
            controller, which returns an internal-server-error response.
    """
    normalized_ids = normalize_image_ids(image_ids)
    storage = UFECLAnnotatorBucket()

    with transaction.atomic():
        image_queryset = ImageInfo.objects.select_for_update().filter(
            image_id__in=normalized_ids
        )
        images = list(image_queryset)
        found_ids = {image.image_id for image in images}
        missing_ids = [
            str(image_id) for image_id in normalized_ids if image_id not in found_ids
        ]
        if missing_ids:
            raise ValueError(f"Images do not exist: {', '.join(missing_ids)}")

        image_urls = UploadedImage.objects.filter(
            image_id_id__in=normalized_ids
        ).values_list("image_url", flat=True)
        for image_url in image_urls:
            storage.delete(storage_key_from_url(image_url, storage.bucket_name))

        image_queryset.delete()

    return [str(image_id) for image_id in normalized_ids]


@route("projects/data/remove-images")
class RemoveImagesController(Controller):
    """Handle ``POST /api/projects/data/remove-images`` requests.

    Expected JSON body::

        {"imageIds": ["image-uuid", "another-image-uuid"]}

    A successful response contains ``deletedImageIds`` and ``deletedCount``.
    """

    def process_post_request(self, request: RemoveImagesRequest):
        """Remove the requested images and build the success response."""
        deleted_image_ids = remove_images(request.image_ids)
        return ok(
            {
                "deletedImageIds": deleted_image_ids,
                "deletedCount": len(deleted_image_ids),
            }
        )
