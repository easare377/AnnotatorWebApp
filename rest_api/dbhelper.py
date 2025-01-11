from .models import *
import uuid
import json
from django.http import JsonResponse
import time
from rest_api.utils import utils as utils
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from .models import Projects, ImageInfo, ProjectSetup, ObjectClass, AnnotationType, ImageType

date_format = '%Y-%m-%d %H:%M:%S'


def add_annotation_type_if_not_exist():
    # Define a namespace and a name (string) to generate the UUID
    namespace = uuid.NAMESPACE_DNS
    polygon_name = "POLYGON"
    bbox_name = "BBOX"
    AnnotationType(annotation_id=uuid.uuid5(namespace, polygon_name), annotation_type='POLYGON').save()
    AnnotationType(annotation_id=uuid.uuid5(namespace, bbox_name), annotation_type='BBOX').save()


def get_projects():
    projects = Projects.objects.all()  # Query all projects from the database
    project_list = []

    for project in projects:
        project_dict = {
            'projectId': str(project.project_id),
            'name': project.project_name,
            'description': project.description,
            'dateCreated': project.date_created.strftime(date_format)
        }
        project_list.append(project_dict)

    return project_list


def get_project_details(project_id):
    project = Projects.objects.get(project_id=project_id)
    project_dict = {
        'projectId': str(project.project_id),
        'name': project.project_name,
        'description': project.description,
        'dateCreated': project.date_created.strftime(date_format)
    }
    return project_dict


def create_project(project_info):
    if not project_info:
        raise ValueError("Project information must be provided")

    project_name = project_info.name
    project_description = project_info.description

    project_setup = project_info.project_setup
    annotation_type = project_setup.annotation_type

    object_classes = project_setup.object_classes

    try:
        with transaction.atomic():
            # Create a new project row
            project_model = Projects(
                project_name=project_name,
                description=project_description
            )
            project_model.save()
            # Create a new project setup row
            annotation_type_instance = AnnotationType.objects.get(annotation_type=annotation_type)
            project_setup_model = ProjectSetup(
                project_id=project_model,  # Using the project instance directly
                annotation_id=annotation_type_instance
            )
            project_setup_model.save()
            # Create new object class rows
            for index, object_class in enumerate(object_classes, start=1):
                class_name = object_class.class_name
                object_class_color = object_class.color
                object_class_description = object_class.description
                # Save new object class row with class_index
                object_class_model = ObjectClass(
                    setup_id=project_setup_model,  # Using the project setup instance directly
                    class_name=class_name,
                    class_index=index,  # Set the class_index to the current loop index
                    color=object_class_color,
                    description=object_class_description
                )
                object_class_model.save()
    except IntegrityError:
        raise ValueError("Failed to create project due to database error")
    return project_model


def get_images(project_id):
    # Query the ImageInfo model for images with the given project_id
    images = ImageInfo.objects.filter(project_id=project_id)
    # Convert the query result to a list of dictionaries
    images_list = []
    for image in images:
        image_dict = {
            'imageId': str(image.image_id),
            'originalFilename': image.original_filename,
            'imageUrl': image.png_image_url,
            'imageWidth': image.image_width,
            'imageHeight': image.image_height,
            'dateAdded': image.date_created.strftime(date_format)
        }
        images_list.append(image_dict)
    return images_list


def __get_uploaded_images_info__(image_id):
    """
    Helper function to retrieve the uploaded image URLs based on the provided image_id.

    Parameters:
    - image_id (UUID): The unique identifier of the image.

    Returns:
    - dict: A dictionary containing the image URLs for different image types.
        - 'png': URL for the PNG version of the image.
        - 'jpg': URL for the JPG version of the image.
        - 'thumb': URL for the thumbnail version of the image.
    """
    uploaded_images = UploadedImage.objects.filter(image_id=image_id)
    image_urls = {
        ImageType.PNG.value.lower(): None,
        ImageType.JPG.value.lower(): None,
        ImageType.THUMB.value.lower(): None
    }

    for uploaded_image in uploaded_images:
        image_type = uploaded_image.image_type.lower()
        if image_type in image_urls:
            image_urls[image_type] = uploaded_image.image_url

    return image_urls


def get_image_info(image_id):
    """
    Retrieves image information based on the provided image_id.

    Parameters:
    - image_id (UUID): The unique identifier of the image.

    Returns:
    - dict: A dictionary containing the image information, which includes:
        - imageId (str): The unique identifier of the image.
        - originalFilename (str): The original filename of the image.
        - imageUrls (dict): The URLs or paths to access the image in different formats (PNG, JPG, THUMB).
        - imageWidth (int): The width of the image in pixels.
        - imageHeight (int): The height of the image in pixels.
        - dateAdded (str): The date and time when the image was added.

    Raises:
    - ImageInfo.DoesNotExist: If the image with the given image_id does not exist.
    """
    try:
        image = ImageInfo.objects.get(image_id=image_id)

        image_dict = {
            'imageId': str(image.image_id),
            'originalFilename': image.original_filename,
            'imageUrls': __get_uploaded_images_info__(image.image_id),
            'imageWidth': image.image_width,
            'imageHeight': image.image_height,
            'dateAdded': image.date_created.strftime(date_format),
        }

        return image_dict

    except ImageInfo.DoesNotExist:
        return None


def save_image_info(project_id, png_image_url, jpg_image_url, thumbnail_url, image_details):
    """
    Save image information and associated uploads to the database atomically.

    Parameters:
    - project_id: The project to which this image belongs.
    - png_image_url: URL to the PNG version of the image.
    - jpg_image_url: URL to the JPG version of the image.
    - thumbnail_url: URL to the thumbnail version of the image.
    - image_details: Object containing image metadata (e.g., file name, width, height).

    Returns:
    - ImageInfo: The created ImageInfo instance.

    Raises:
    - ValueError: If any of the operations fail.
    """
    try:
        with transaction.atomic():
            # Fetch the project instance
            project_instance = Projects.objects.get(project_id=project_id)

            # Create the ImageInfo instance
            image_info = ImageInfo.objects.create(
                image_id=uuid.uuid4(),
                project_id=project_instance,
                original_filename=image_details.file_name,
                image_width=image_details.width,
                image_height=image_details.height,
                date_created=timezone.now()
            )

            # Save associated uploaded images (PNG, JPG, THUMB)
            __save_upload_info__(image_info.image_id, png_image_url, ImageType.PNG)
            __save_upload_info__(image_info.image_id, jpg_image_url, ImageType.JPG)
            __save_upload_info__(image_info.image_id, thumbnail_url, ImageType.THUMB)

            return image_info

    except Projects.DoesNotExist:
        raise ValueError(f"Project with ID {project_id} does not exist.")
    except Exception as e:
        raise ValueError(f"Failed to save image info: {str(e)}")


def __save_upload_info__(image_id, image_url, image_type: ImageType):
    """
    Save image upload information to the UploadedImage model.

    Parameters:
    - image_id (UUID): The ID of the related image.
    - image_url (str): The URL of the uploaded image.
    - image_type (ImageType): The type of the image (e.g., JPG, PNG, THUMB).

    Returns:
    - UploadedImage: The created UploadedImage instance.
    """
    try:
        uploaded_image = UploadedImage.objects.create(
            image_id_id=image_id,  # Use the ForeignKey field directly
            image_url=image_url,
            image_type=image_type.value  # Use the enum's value
        )
        return uploaded_image
    except Exception as e:
        raise ValueError(f"Failed to save upload info: {str(e)}")


def __save_polygon_info__(image_id, polygon_info):
    """
    Save a new polygon instance to the database.

    Parameters:
    - image_id: The ID of the related image.
    - polygon_info: An object containing the polygon's points, stability score, and predicted IOU.

    The polygon_info object should have the following attributes:
    - points: Array of points defining the polygon shape.
    - stability_score: Stability score associated with the polygon.
    - predicted_iou: Predicted intersection over union (IOU) value for the polygon.
    """
    # Validate the points format
    if not utils.validate_points(polygon_info.points):
        raise ValidationError("points must be in the format [{'x': int, 'y': int}, {'x': int, 'y': int}, {'x': int, "
                              "'y': int}].")

    # Fetch the ImageInfo instance
    try:
        image_instance = ImageInfo.objects.get(image_id=image_id)
    except ImageInfo.DoesNotExist:
        raise ValidationError(f"Image with ID {image_id} does not exist.")

    # Save the polygon instance
    polygon = Polygons(
        image_id=image_instance,  # Use the ImageInfo instance
        points=polygon_info.points,
        stability_score=polygon_info.stability_score,
        predicted_iou=polygon_info.predicted_iou,
        date_created=timezone.now(),
        date_modified=timezone.now()
    )
    polygon.save()

    polygon_dict = {
        'polygonId': str(polygon.polygon_id),
        'classId': str(polygon.class_id_id),
        'points': polygon.points,
        'stabilityScore': polygon.stability_score,
        'predictedIoU': polygon.predicted_iou,
        'dateCreated': polygon.date_created.strftime(date_format),
        'dateModified': polygon.date_modified.strftime(date_format)
    }
    return polygon_dict


def save_polygon_infos(image_id, polygon_infos):
    """
    Save multiple polygon instances to the database in an atomic operation.

    Parameters:
    - image_id: The ID of the related image.
    - polygon_infos: A list of objects, each containing the polygon's points, stability score, and predicted IOU.

    Each polygon_info object should have the following attributes:
    - points: Array of points defining the polygon shape.
    - stability_score: Stability score associated with the polygon.
    - predicted_iou: Predicted intersection over union (IOU) value for the polygon.
    """
    try:
        db_polygon_infos = []
        with transaction.atomic():
            for polygon_info in polygon_infos:
                polygon_info_dict = __save_polygon_info__(image_id, polygon_info)
                db_polygon_infos.append(polygon_info_dict)
        return db_polygon_infos
    except ValidationError as e:
        raise e
    except Exception as e:
        # Log the exception (optional)
        print(f'Error: {e}')
        raise ValueError("Failed to save polygons due to a database error.")


def get_project_setup(project_id):
    """
    Retrieves the project setup details including annotation type, object classes, and image information.

    Parameters:
    - project_id (UUID): The unique identifier of the project.

    Returns:
    - dict: A dictionary containing the project setup details, which includes:
        - annotationType (dict): Information about the annotation type.
            - annotationId (str): The unique identifier of the annotation type.
            - annotationType (str): The type of annotation.
        - objectClasses (list): A list of dictionaries containing object class details.
            - setupId (str): The unique identifier of the project setup.
            - className (str): The name of the object class.
            - color (str): The color associated with the object class.
            - description (str): A description of the object class.
        - imageInfos (list): A list of dictionaries containing image information.
            - imageId (str): The unique identifier of the image.
            - originalFilename (str): The original filename of the image.
            - imageUrl (str): The URL or path to access the image.
            - imageWidth (int): The width of the image in pixels.
            - imageHeight (int): The height of the image in pixels.
            - dateAdded (str): The date and time when the image was added.
            - dateModified (str): The date and time when the image was last modified.

    Raises:
    - Projects.DoesNotExist: If the project with the given project_id does not exist.
    """
    project = Projects.objects.get(project_id=project_id)

    # Get ProjectSetup related to the project
    project_setup = ProjectSetup.objects.get(project_id=project)
    annotation_type = project_setup.annotation_id

    # Get ObjectClasses related to the project setup
    object_classes = ObjectClass.objects.filter(setup_id=project_setup)
    object_classes_list = [
        {
            'classId': str(obj_class.class_id),
            'className': obj_class.class_name,
            'classIndex': obj_class.class_index,
            'color': obj_class.color,
            'description': obj_class.description
        }
        for obj_class in object_classes
    ]
    return {
        'setupId': str(project_setup.setup_id),
        'annotationType': annotation_type.annotation_type,
        'objectClasses': object_classes_list
    }


def get_polygons(image_id):
    # Query the Polygons model for polygons with the given image_id
    polygons = Polygons.objects.filter(image_id=image_id)
    # Convert the query result to a list of dictionaries
    polygons_list = []
    for polygon in polygons:
        polygon_dict = {
            'polygonId': str(polygon.polygon_id),
            'classId': str(polygon.class_id_id),
            'points': polygon.points,
            'stabilityScore': polygon.stability_score,
            'predictedIoU': polygon.predicted_iou,
            'dateCreated': polygon.date_created.strftime(date_format),
            'dateModified': polygon.date_modified.strftime(date_format)
        }
        polygons_list.append(polygon_dict)
    return polygons_list


def get_annotated_polygons(image_id):
    """
    Retrieve annotated polygons for a given image_id and convert them to a list of dictionaries.
    An annotated polygon is defined as having a non-null class_id.

    Args:
    - image_id (int): The ID of the image for which to retrieve annotated polygons.

    Returns:
    - list: A list of dictionaries containing annotated polygon details.
    """
    # Query the Polygons model for annotated polygons with the given image_id
    annotated_polygons = Polygons.objects.filter(image_id=image_id, class_id__isnull=False)
    # Convert the query result to a list of dictionaries
    annotated_polygons_list = []
    for polygon in annotated_polygons:
        polygon_dict = {
            'polygonId': str(polygon.polygon_id),
            'classId': str(polygon.class_id_id),
            'points': polygon.points,
            'stabilityScore': polygon.stability_score,
            'predictedIoU': polygon.predicted_iou,
            'dateCreated': polygon.date_created.strftime(date_format),
            'dateModified': polygon.date_modified.strftime(date_format)
        }
        annotated_polygons_list.append(polygon_dict)
    return annotated_polygons_list


def save_or_update_object_class(polygon_id, class_id):
    """
    Save or update the object class for a given polygon.

    Parameters:
    - polygon_id: The unique identifier of the polygon.
    - class_id: The unique identifier of the object class.

    Returns:
    - dict: A dictionary containing the updated polygon details.

    Raises:
    - Polygons.DoesNotExist: If the polygon with the given polygon_id does not exist.
    - ObjectClass.DoesNotExist: If the object class with the given class_id does not exist.
    - Exception: If there is a general error during the operation.
    """
    try:
        # Fetch the polygon instance
        polygon = Polygons.objects.get(polygon_id=polygon_id)

        # Fetch the object class instance
        object_class = ObjectClass.objects.get(class_id=class_id)

        # Update the polygon's class_id
        polygon.class_id = object_class
        polygon.save()
    except Polygons.DoesNotExist:
        raise ObjectDoesNotExist(f"Polygon with ID {polygon_id} does not exist.")

    except ObjectClass.DoesNotExist:
        raise ObjectDoesNotExist(f"Object class with ID {class_id} does not exist.")

    except Exception as e:
        raise Exception(f"An error occurred while saving or updating the object class: {str(e)}")


def save_or_update_object_classes(object_class_infos):
    """
    Save or update the object classes for multiple polygons.

    Parameters:
    - polygon_ids: A list of unique identifiers of the polygons.
    - class_ids: A list of unique identifiers of the object classes.

    Raises:
    - ValueError: If the lengths of polygon_ids and class_ids do not match.
    - Polygons.DoesNotExist: If any of the polygons with the given polygon_ids do not exist.
    - ObjectClass.DoesNotExist: If any of the object classes with the given class_ids do not exist.
    - Exception: If there is a general error during the operation.
    """
    # if len(polygon_ids) != len(class_ids):
    #     raise ValueError("The lengths of polygon_ids and class_ids must match.")
    with transaction.atomic():
        for object_class_info in object_class_infos:
            polygon_id = object_class_info.polygon_id
            class_id = object_class_info.class_id
            save_or_update_object_class(polygon_id, class_id)


def get_object_classes(project_id):
    """
    Retrieves the object classes associated with a specific project.

    Parameters:
    - project_id (UUID): The unique identifier of the project.

    Returns:
    - list: A list of dictionaries containing object class details.
    """
    try:
        # Assuming object classes are related via ProjectSetup
        project_setup = ProjectSetup.objects.get(project_id=project_id)
        object_classes = ObjectClass.objects.filter(setup_id=project_setup)

        object_class_list = [
            {
                'classId': str(obj_class.class_id),
                'className': obj_class.class_name,
                'color': obj_class.color,
                'description': obj_class.description
            }
            for obj_class in object_classes
        ]
        return object_class_list

    except ProjectSetup.DoesNotExist:
        raise ValidationError(f"Project setup with project ID {project_id} does not exist.")
    except Exception as e:
        raise Exception(f"An error occurred while retrieving object classes: {str(e)}")


def get_object_class(class_id):
    """
    Retrieves the details of a specific object class by its class ID.

    Parameters:
    - classId (UUID or str): The unique identifier of the object class.

    Returns:
    - dict: A dictionary containing object class details.
    """
    try:
        # Assuming classId is a UUID or string that matches the class_id in ObjectClass
        obj_class = ObjectClass.objects.get(class_id=class_id)

        object_class_details = {
            'classId': str(obj_class.class_id),
            'className': obj_class.class_name,
            'color': obj_class.color,
            'description': obj_class.description
        }

        return object_class_details

    except ObjectClass.DoesNotExist:
        raise ValidationError(f"Object class with ID {class_id} does not exist.")
    except Exception as e:
        raise Exception(f"An error occurred while retrieving the object class: {str(e)}")


def create_export_details(project_id, zip_file_url):
    """
    Creates a new export detail record in the database.
    Parameters:
    - project_id (UUID): The UUID of the project associated with the export.
    - zip_file_url (str): The URL where the exported zip file is stored.
    Returns:
    - ExportDetails: The created ExportDetails object.
    """
    # Ensure the project exists
    project = Projects.objects.get(project_id=project_id)
    # Create a new export details entry
    export_details = ExportDetails.objects.create(
        project_id=project,
        zip_file_url=zip_file_url,
        date_created=timezone.now()
    )
    return export_details


def save_exported_data(export_id, annotation_file_url, rgb_file_url=None):
    """
    Saves exported data files to the database.
    Parameters:
    - export_id (UUID): The UUID of the export operation associated with these files.
    - mask_file_url (str): The URL where the mask file is stored.
    - rgb_file_url (str): The URL where the RGB file is stored.

    Returns:
    - ExportedData: The created ExportedData object.
    """
    # Ensure the export exists
    export_details = ExportDetails.objects.get(export_id=export_id)
    # Create a new exported data entry
    exported_data = ExportedData.objects.create(
        export_id=export_details,
        annotation_file_url=annotation_file_url,
        rgb_file_url=rgb_file_url,
        date_created=timezone.now()
    )
    return exported_data


def delete_project(project_id):
    """
    Delete a project and all related data from the database.
    Parameters:
    - project_id: The ID of the project to delete.
    Raises:
    - ObjectDoesNotExist: If the project with the given ID does not exist.
    """
    # Use a transaction to ensure all related data is deleted atomically
    # Use a transaction to ensure all related data is deleted atomically
    with transaction.atomic():
        # Fetch the project to ensure it exists
        project = Projects.objects.get(project_id=project_id)
        # Delete related ExportedData and ExportDetails
        for export_detail in ExportDetails.objects.filter(project_id=project):
            ExportedSegmentationData.objects.filter(export_id=export_detail).delete()
            export_detail.delete()
        # Delete all related Polygon objects
        polygons = Polygons.objects.filter(image_id__project_id=project)
        polygons.delete()
        # Delete all related ObjectClass objects
        object_classes = ObjectClass.objects.filter(setup_id__project_id=project)
        object_classes.delete()
        # Delete all related ProjectSetup objects
        ProjectSetup.objects.filter(project_id=project).delete()
        # Delete all related ImageInfo objects
        ImageInfo.objects.filter(project_id=project).delete()
        # Finally, delete the project itself
        project.delete()
        # print(f"Project with ID {project_id} and all related data have been deleted successfully.")
