"""Receive an original image through a signed local upload URL."""

import tempfile
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

from ..controller import Controller, HttpResponseObject, ok
from ..decorators.route import route
from ..models import ImageInfo
from ..objects.enums.image_status import ImageStatus
from .generate_upload_image_link_controller import (
    UPLOAD_LINK_SALT,
    original_image_storage_key,
)


DEFAULT_MAX_UPLOAD_BYTES = 100 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 64 * 1024


class ImageUploadTooLargeError(Exception):
    """Raised when an upload exceeds the configured size limit while streaming."""


def original_image_upload_directory() -> Path:
    """Return the local directory used for raw uploaded image objects."""
    return Path(settings.BASE_DIR) / "uploads" / "original"


def ensure_original_image_upload_directory() -> Path:
    """Create and return the local directory used for original image uploads."""
    upload_directory = original_image_upload_directory()
    upload_directory.mkdir(parents=True, exist_ok=True)
    return upload_directory


def is_valid_upload_token(image_id: UUID, token: str | None) -> bool:
    """Check that the URL was issued for this image ID and has not expired."""
    if not token:
        return False

    signer = TimestampSigner(salt=UPLOAD_LINK_SALT)
    max_age = getattr(settings, "LOCAL_UPLOAD_LINK_MAX_AGE_SECONDS", 15 * 60)
    try:
        return signer.unsign(token, max_age=max_age) == str(image_id)
    except (BadSignature, SignatureExpired):
        return False


def write_uploaded_image(uploaded_image, destination: Path, max_upload_bytes: int) -> int:
    """Write an uploaded image atomically and return the number of bytes stored."""
    temporary_path = None
    bytes_written = 0

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            for chunk in uploaded_image.chunks(UPLOAD_CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > max_upload_bytes:
                    raise ImageUploadTooLargeError()
                temporary_file.write(chunk)

        if bytes_written == 0:
            raise ValueError("The uploaded image is empty.")

        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return bytes_written


@route("projects/data/upload-image/<uuid:image_id>")
class UploadImageController(Controller):
    """Store a multipart image locally through the common controller flow."""

    http_method_names = ["post", "options"]

    def process_post_request(self, request_object):
        image_id = self.kwargs["image_id"]
        # Validate the token to ensure the upload URL is valid and not expired
        token = getattr(request_object, "token", None) or self.request.GET.get("token")
        if not is_valid_upload_token(image_id, token):
            return HttpResponseObject(
                403,
                body={"error": "Invalid or expired upload URL."},
            )
        # Ensure uploaded file is a valid image
        uploaded_image = request_object.image
        if not (uploaded_image.content_type or "").lower().startswith("image/"):
            raise ValueError("The uploaded file must be an image.")
        # Verify the file does not exceed the maximum allowed size
        max_upload_bytes = getattr(
            settings,
            "LOCAL_UPLOAD_MAX_BYTES",
            DEFAULT_MAX_UPLOAD_BYTES,
        )
        if uploaded_image.size > max_upload_bytes:
            return HttpResponseObject(
                413,
                body={"error": "Image exceeds the upload-size limit."},
            )
        # Create the upload directory if it doesn't exist
        upload_directory = ensure_original_image_upload_directory()
        destination = upload_directory / str(image_id)
        # Write the uploaded image to the destination path, handling any errors
        try:
            bytes_written = write_uploaded_image(
                uploaded_image,
                destination,
                max_upload_bytes,
            )
        except ImageUploadTooLargeError:
            return HttpResponseObject(
                413,
                body={"error": "Image exceeds the upload-size limit."},
            )

        ImageInfo.objects.filter(image_id=image_id).update(status=ImageStatus.UPLOADED)

        return ok(
            {
                "imageId": str(image_id),
                "storageKey": original_image_storage_key(str(image_id)),
                "bytesUploaded": bytes_written,
            }
        )
