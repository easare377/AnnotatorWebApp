from django.db import models


class ImageType(models.TextChoices):
    JPG = "JPG"
    PNG = "PNG"
    THUMB = "THUMB"
