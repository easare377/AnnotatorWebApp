from .models import *
import uuid
import json
from django.http import JsonResponse
import time
from rest_api.utils import utils as utils
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError

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


from django.db import transaction
from django.db.utils import IntegrityError
from .models import Projects, ImageInfo, ProjectSetup, ObjectClass, AnnotationType


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
            annotation_type_map = {
                "POLYGON": "092cfa2c-371d-516e-8eb7-776931146fd6",
                "BBOX": "858bdea9-94b8-5e1d-8339-03d14b75ca41"
            }
            annotation_type_instance = AnnotationType.objects.get(annotation_id=annotation_type_map[annotation_type])
            project_setup_model = ProjectSetup(
                project_id=project_model,  # Using the project instance directly
                annotation_id=annotation_type_instance
            )
            project_setup_model.save()

            # Create new object class rows
            for object_class in object_classes:
                class_name = object_class.class_name
                object_class_color = object_class.color
                object_class_description = object_class.description
                # Save new object class row
                object_class_model = ObjectClass(
                    setup_id=project_setup_model,  # Using the project setup instance directly
                    class_name=class_name,
                    color=object_class_color,
                    description=object_class_description,
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
            'imageUrl': image.image_url,
            'imageWidth': image.image_width,
            'imageHeight': image.image_height,
            'dateAdded': image.date_added.strftime(date_format),
            'dateModified': image.date_modified.strftime(date_format)
        }
        images_list.append(image_dict)

    return images_list


def get_image_info(image_id):
    """
    Retrieves image information based on the provided image_id.

    Parameters:
    - image_id (UUID): The unique identifier of the image.

    Returns:
    - dict: A dictionary containing the image information, which includes:
        - imageId (str): The unique identifier of the image.
        - originalFilename (str): The original filename of the image.
        - imageUrl (str): The URL or path to access the image.
        - imageWidth (int): The width of the image in pixels.
        - imageHeight (int): The height of the image in pixels.
        - dateAdded (str): The date and time when the image was added.
        - dateModified (str): The date and time when the image was last modified.

    Raises:
    - ImageInfo.DoesNotExist: If the image with the given image_id does not exist.

    Example:
    >>> get_image_info('19699044-5ada-4a1b-8924-a523dac47618')
    {
        'imageId': '19699044-5ada-4a1b-8924-a523dac47618',
        'originalFilename': 'image.jpg',
        'imageUrl': 'https://s3.bucket/19699044-5ada-4a1b-8924-a523dac47618.png',
        'imageWidth': 3000,
        'imageHeight': 2000,
        'dateAdded': '2020-02-02 13:30:23',
        'dateModified': '2020-02-02 13:30:23'
    }
    """
    try:
        image = ImageInfo.objects.get(image_id=image_id)
        image_dict = {
            'imageId': str(image.image_id),
            'originalFilename': image.original_filename,
            'imageUrl': image.image_url,
            'imageWidth': image.image_width,
            'imageHeight': image.image_height,
            'dateAdded': image.date_added.strftime(date_format),
            'dateModified': image.date_modified.strftime(date_format)
        }
        return image_dict

    except ImageInfo.DoesNotExist:
        return None


def save_image_info(project_id, image_url, image_details):
    """
    Save image information to the database.

    Parameters:
    - project_id: The project to which this image belongs.
    - original_filename: The original filename of the image.
    - image_url: The URL or path to access the image.
    - image_width: The width of the image in pixels.
    - image_height: The height of the image in pixels.

    Returns:
    - image_info: The created ImageInfo instance.
    """
    original_filename = image_details.file_name
    image_width = image_details.width
    image_height = image_details.height
    #
    project_instance = Projects.objects.get(project_id=project_id)
    # Create a new ImageInfo instance
    image_info = ImageInfo(
        image_id=uuid.uuid4(),
        project_id=project_instance,
        original_filename=original_filename,
        image_url=image_url,
        image_width=image_width,
        image_height=image_height,
        date_added=timezone.now(),
        date_modified=timezone.now()
    )
    # Save the instance to the database
    image_info.save()

    return image_info


def update_project_with_details(self, request_object):
    # if request.method == 'POST':
    try:
        data = request_object
        project_id = data['project_id']

        # Fetch the project by project_id
        try:
            project = Projects.objects.get(project_id=project_id)

        except Projects.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Update project fields
        project.project_name = data.get('project_name', project.project_name)
        project.description = data.get('project_description', project.description)
        project.last_modified = timezone.now()
        project.save()

        # Update ImageInfo (assuming one image per project for simplicity)
        try:
            image_info = ImageInfo.objects.get(project_id=project)
            image_info.original_filename = data.get('original_filename', image_info.original_filename)
            image_info.date_modified = timezone.now()
            image_info.save()
        except ImageInfo.DoesNotExist:
            return JsonResponse({'error': 'ImageInfo not found'}, status=404)

        # Handle annotation type
        annotation_type_map = {
            "POLYGON": "092cfa2c-371d-516e-8eb7-776931146fd6",
            "BBOX": "858bdea9-94b8-5e1d-8339-03d14b75ca41"
        }
        annotation_type_key = data.get('annotation_type', 'POLYGON')  # Use 'POLYGON' as default
        annotation_type_uuid = annotation_type_map.get(annotation_type_key, annotation_type_map['POLYGON'])
        print(annotation_type_uuid)

        # Get or create the AnnotationType
        annotation_type, created = AnnotationType.objects.get_or_create(
            annotation_id=annotation_type_uuid,
            defaults={'annotation_type': annotation_type_key}
        )
        # print(annotation_type)

        # Update AnnotationSetup (assuming one setup per image for simplicity)
        try:
            annotation_setup = AnnotationSetup.objects.get(image_id=image_info)
            annotation_setup.annotation_type = annotation_type
            annotation_setup.save()
        except AnnotationSetup.DoesNotExist:
            return JsonResponse({'error': 'AnnotationSetup not found'}, status=404)

        # Update ObjectClass instances
        class_names = data.get('class_name', [])
        colors = data.get('color', [])
        description = data.get('description', '')

        # Clear existing ObjectClass instances
        ObjectClass.objects.filter(setup_id_id=annotation_setup).delete()

        # Create new ObjectClass instances
        for class_name, color in zip(class_names, colors):
            object_class = ObjectClass(
                setup_id=annotation_setup,
                class_name=class_name,
                color=color,
                description=description  # Assuming single description for all
            )
            object_class.save()

        return JsonResponse({'message': 'Project and related data updated successfully'}, status=200)
    except KeyError as e:
        return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_project_details():
    pass


def delete_project_details(self, request_object):
    try:
        data = request_object
        project_id = data['project_id']

        try:
            project = Projects.objects.get(project_id=project_id)
            images = ImageInfo.objects.filter(project_id=project_id)
        except Exception as e:
            return e
        if len(images) == 1:
            image = images[0]
            image.delete()
            print("Image deleted")
        project.delete()
        return JsonResponse({'message': 'Project deleted successfully'})
    except Projects.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)


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
    # project_setup = ProjectSetup.objects.filter(project_id=project).select_related('annotation_id')
    project_setup = ProjectSetup.objects.get(project_id=project)
    # project_setup = project_setup.first()

    # Get AnnotationType
    # 'annotationId': str(project_setup.annotation_id),
    annotation_type = project_setup.annotation_id
    # annotation_type = {
    #     'annotationType': project_setup.annotation_id
    # }

    # Get ObjectClasses related to the project setup
    object_classes = ObjectClass.objects.filter(setup_id=project_setup)
    object_classes_list = [
        {
            'classId': str(obj_class.class_id),
            'className': obj_class.class_name,
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
#
# # image_info = ImageInfo()
#
# # def update_project(self, project_name, description=None):
# #     projects = Projects()
# #     projects.
#
# def get_projects_info(project_id):
#     projects = Projects.objects.all()
#     return projects
