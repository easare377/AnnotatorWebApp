from django.db import models


class ImageStatus(models.TextChoices):
    """Lifecycle states for an image upload and its local/S3 processing.

    ``PENDING``
        The upload was created, but the original image has not been confirmed.
    ``UPLOADED``
        The original image was uploaded successfully and is ready for processing.
    ``PROCESSING``
        The PNG, JPG, and thumbnail versions are being generated.
    ``COMPLETED``
        Processing finished and all image records are ready for use.
    ``FAILED``
        Upload finalization or image processing failed.
    ``CANCELED``
        The upload was deliberately stopped before it completed.
    ``EXPIRED``
        The upload was not completed before its allowed expiration time.

    ``COMPLETED``, ``FAILED``, ``CANCELED``, and ``EXPIRED`` are terminal
    states.
    """

    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"
