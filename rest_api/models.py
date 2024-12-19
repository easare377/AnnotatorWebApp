from django.db import models
import uuid
from django.utils import timezone


class Projects(models.Model):
    """
    Represents a table used to store projects.

    Fields:
    - project_id: Unique identifier for the project.
    - project_name: Name of the project.
    - description: Description of the project.
    - date_created: Date and time when the project was created.
    - last_modified: Date and time when the project was last modified.
    """
    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_name = models.CharField(max_length=50, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now, null=False)


class ImageInfo(models.Model):
    """
    Represents a table used to store image information.

    Fields:
    - image_id: Unique identifier for the image.
    - project_id: Foreign key to relate the image to a project.
    - original_filename: Original filename of the image.
    - image_url: URL or path to access the image.
    - image_width: Width of the image in pixels.
    - image_height: Height of the image in pixels.
    - date_added: Date and time when the image was added.
    - date_modified: Date and time when the image was last modified.
    """
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, null=False)
    original_filename = models.CharField(max_length=10000, null=False)
    png_image_url = models.CharField(max_length=1000, null=False)
    jpg_image_url = models.CharField(max_length=1000, null=False)
    image_width = models.IntegerField(null=False)
    image_height = models.IntegerField(null=False)
    date_created = models.DateTimeField(default=timezone.now, null=False)


class AnnotationType(models.Model):
    """
    Represents a table used to store annotation types.

    Fields:
    - annotation_id: Unique identifier for the annotation type.
    - annotation_type: Type of annotation.
    """
    annotation_id = models.UUIDField(primary_key=True, editable=False)
    annotation_type = models.CharField(max_length=20, null=False)


class ProjectSetup(models.Model):
    """
    Represents a table used to set up annotations for images.

    Fields:
    - setup_id: Unique identifier for the annotation setup.
    - image_id: Foreign key to relate the setup to an image.
    - annotation_type: Foreign key to relate the setup to an annotation type.
    """
    setup_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, null=False)
    annotation_id = models.ForeignKey(AnnotationType, on_delete=models.CASCADE)


class ObjectClass(models.Model):
    """
    Represents a table used to store object classes for annotations.

    Fields:
    - class_id: Unique identifier for the object class.
    - setup_id: Foreign key to relate the class to an annotation setup.
    - class_name: Name of the object class.
    - color: Color associated with the object class.
    - description: Description of the object class.
    - class_index: An integer representing the index of the object class.
    """
    class_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    setup_id = models.ForeignKey(ProjectSetup, on_delete=models.CASCADE, null=False)
    class_name = models.CharField(max_length=50, null=False)
    class_index = models.IntegerField(null=False)
    color = models.CharField(max_length=7, null=False)
    description = models.CharField(max_length=255, blank=True)


class Polygons(models.Model):
    """
    Represents a table used to store polygons.

    Fields:
    - polygon_id: Unique identifier for the polygon.
    - image_id: Foreign key to relate the polygon to an image.
    - class_id: Foreign key to relate the polygon to an object class (nullable).
    - points: Array of points defining the polygon shape.
    - stability_score: Stability score associated with the polygon.
    - predicted_iou: Predicted intersection over union (IOU) value for the polygon.
    - date_created: Date and time when the polygon was created.
    - date_modified: Date and time when the polygon was last modified.
    """
    polygon_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_id = models.ForeignKey(ImageInfo, on_delete=models.CASCADE, null=False)
    class_id = models.ForeignKey(ObjectClass, on_delete=models.CASCADE, null=True, blank=True)
    points = models.JSONField(null=False)
    stability_score = models.FloatField(null=False)
    predicted_iou = models.FloatField(null=False)
    date_created = models.DateTimeField(default=timezone.now, null=False)
    date_modified = models.DateTimeField(auto_now=True)


class ExportDetails(models.Model):
    """
    Represents a table used to store project export details.

    Fields:
    - export_id: Unique identifier for the export.
    - project_id: Foreign key to relate the export to a project.
    - date_created: Date and time when the export was created.
    """
    export_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, null=False)
    zip_file_url = models.CharField(max_length=1000, null=False)
    date_created = models.DateTimeField(default=timezone.now, null=False)


class ExportedData(models.Model):
    """
        Model representing the exported data files for a given export operation.

        Attributes:
            id (UUIDField): A unique identifier for each record.
            export_id (ForeignKey): A foreign key reference to the `ExportDetails` model.
            annotation_file_url (CharField): The URL path to the file containing the annotation associated with this export.
            rgb_file_url (CharField): The URL path to the RGB file associated with this export.
            date_created (DateTimeField): The timestamp when this record was created.
        """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export_id = models.ForeignKey(ExportDetails, on_delete=models.CASCADE, null=False)
    annotation_file_url = models.CharField(max_length=1000, null=False)
    rgb_file_url = models.CharField(max_length=1000, null=True)
    date_created = models.DateTimeField(default=timezone.now, null=False)

