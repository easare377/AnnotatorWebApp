"""Create short-lived local upload URLs for original image files.

The returned URLs use the same shape as a presigned storage upload: the client
receives an object key and uploads its image directly to that one URL. This
local implementation accepts multipart POST requests and is independent of the
image-processing and database workflows.
"""

from urllib.parse import urlencode

from django.conf import settings
from django.core.signing import TimestampSigner

from ..controller import Controller, ok
from ..decorators.route import route
from ..objects.url_paths import ORIGINAL_UPLOADS_PATH
from rest_api import dbhelper as dbh


UPLOAD_LINK_SALT = "rest_api.local-image-upload"
DEFAULT_MAX_UPLOAD_LINKS_PER_REQUEST = 100


def original_image_storage_key(image_id: str) -> str:
    """Return the local-storage key for an image awaiting conversion."""
    return str(ORIGINAL_UPLOADS_PATH / image_id)


def validate_upload_count(upload_count) -> int:
    """Validate and return the requested number of upload links."""
    max_uploads = getattr(
        settings,
        "LOCAL_UPLOAD_MAX_LINKS_PER_REQUEST",
        DEFAULT_MAX_UPLOAD_LINKS_PER_REQUEST,
    )

    if isinstance(upload_count, bool) or not isinstance(upload_count, int):
        raise ValueError("uploadCount must be an integer.")
    if not 1 <= upload_count <= max_uploads:
        raise ValueError(f"uploadCount must be between 1 and {max_uploads}.")

    return upload_count


def make_upload_link(request, image_id: str) -> dict:
    """Build a signed, short-lived upload URL for one pending image."""
    signer = TimestampSigner(salt=UPLOAD_LINK_SALT)
    token = signer.sign(image_id)
    relative_url = f"/api/projects/data/upload-image/{image_id}"
    upload_url = request.build_absolute_uri(
        f"{relative_url}?{urlencode({'token': token})}"
    )

    return {
        "imageId": image_id,
        "storageKey": original_image_storage_key(image_id),
        "uploadUrl": upload_url,
        "method": "POST",
    }


@route("projects/data/generate-upload-image-link")
class GenerateUploadImageLinkController(Controller):
    """Create pending image records and return direct local upload URLs.

    Request body::

        {
            "projectId": "project-uuid",
            "images": [
                {
                    "imageDetails": {
                        "fileName": "image.png",
                        "width": 1920,
                        "height": 1080
                    }
                }
            ]
        }

    The base ``Controller`` parses the JSON body and converts camel-case keys
    to the request object's snake-case attributes.
    """

    def process_post_request(self, request_object):
        # Get upload details
        project_id = request_object.project_id
        images = request_object.images
        validate_upload_count(len(images))

        # Save pending image records and use their IDs for the original files.
        image_infos = []
        for image in images:
            image_details = image.image_details
            image_id = str(dbh.save_image_info(project_id, image_details).image_id)
            upload_link = make_upload_link(self.request, image_id)
            image_infos.append(
                {
                    "imageId": image_id,
                    "uploadLink": upload_link,
                }
            )
        return ok({"uploads": image_infos})
