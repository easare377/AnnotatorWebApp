from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh
from ..objects.export_project_details import ExportProjectDetails
from rest_api.utils import utils
import cv2
import numpy as np
from PIL import Image
from ..s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket
import io
from urllib.parse import urlparse
import os
import requests
import zipfile
import uuid


def convert_np_image_to_io(np_image):
    # Convert the NumPy array to a PIL Image
    image = Image.fromarray(np_image)
    # Save the image to an in-memory file
    in_mem_file = io.BytesIO()
    image.save(in_mem_file, format="PNG")
    in_mem_file.seek(0)  # Seek to the start of the file
    return in_mem_file


def extract_filename_from_url(url: str) -> str:
    """
    Extracts the filename without the extension from a given URL.

    Args:
        url (str): The URL from which to extract the filename.

    Returns:
        str: The filename without the extension.
    """
    # Parse the URL to get the path
    path = urlparse(url).path
    # Extract the filename with extension
    filename_with_extension = os.path.basename(path)
    # Remove the extension
    filename, _ = os.path.splitext(filename_with_extension)
    return filename


def create_class_map(class_value_dict, object_classes):
    """
    Create a class map that associates class_values with their corresponding colors.

    Parameters:
        class_value_dict (list): A list of dictionaries with 'class_id' and 'class_value' keys.
        object_classes (list): A list of dictionaries representing object classes with
                               'classId', 'className', 'color', and 'description'.

    Returns:
        list: A list of dictionaries with 'class_value' and 'color' keys.
    """
    class_map = [{'class_value': 0, 'color': [0, 0, 0]}]  # Initialize with the background as black

    # Convert the list of dictionaries to a dictionary for faster lookup
    class_value_lookup = {item['class_id']: item['class_value'] for item in class_value_dict}

    for obj_class in object_classes:
        class_id = obj_class['classId']
        if class_id in class_value_lookup:
            class_value = class_value_lookup[class_id]
            color = utils.hex_to_rgb(obj_class['color'])
            class_map.append({'class_value': class_value, 'color': color})

    return class_map


def get_class_value(class_value_dict, class_id):
    """
    Retrieve the class_value for a given class_id from the class_value_dict.

    Parameters:
        class_value_dict (list): A list of dictionaries with 'class_id' and 'class_value' keys.
        class_id (str): The class_id for which the class_value is needed.

    Returns:
        int or None: The class_value corresponding to the class_id, or None if not found.
    """
    for item in class_value_dict:
        if item['class_id'] == class_id:
            return item['class_value']
    return None


def export_images_to_zip(image_mask_urls):
    # Create an in-memory byte stream to store the ZIP file
    zip_buffer = io.BytesIO()
    count = 1
    # Initialize the ZipFile object
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for image_mask_url in image_mask_urls:
            image_url = image_mask_url['image_url']
            voc_url = image_mask_url['voc_url']
            # rgb_mask_url = image_mask_url['rgb_mask_url']
            # Download the image
            image_response = requests.get(image_url)
            # Download the mask
            voc_response = requests.get(voc_url)
            # Download the rgb mask
            # rgb_mask_response = requests.get(rgb_mask_url)
            if image_response.status_code == 200 and voc_response.status_code == 200:
                image_data = image_response.content
                voc_data = voc_response.content
                # rgb_mask_data = rgb_mask_response.content
                # Extract the image filename from the URL
                # Store the image in the "real" folder in the ZIP
                zip_file.writestr(f'images/{str(count)}.png', image_data)
                # Store the mask in the "mask" folder in the ZIP
                zip_file.writestr(f'labels/{str(count)}.xml', voc_data)
                # Store the rgb mask in the "mask" folder in the ZIP
                # zip_file.writestr(f'rgb/{str(count)}.png', rgb_mask_data)
                count += 1
            else:
                print(f"Failed to download image from {image_url}")
    # Return the in-memory ZIP file
    zip_buffer.seek(0)
    return zip_buffer


def get_class_name_by_id(object_class_list, class_id):
    """
    Retrieves the class name from the object class list using the classId.

    Parameters:
    - object_class_list (list): A list of dictionaries containing object class details.
    - classId (str): The unique identifier of the object class.

    Returns:
    - str: The class name associated with the classId.
    """
    for obj_class in object_class_list:
        if obj_class['classId'] == str(class_id):
            return obj_class['className']

    # If classId is not found, raise an exception or return a default message
    raise ValueError(f"Class with ID {class_id} not found.")


@route('projects/data/export/export-data-voc')
class ExportDataVocController(Controller):

    def process_post_request(self, project_details: ExportProjectDetails):
        project_id = project_details.project_id
        project = dbh.get_project_details(project_id)
        project_name = project['name']
        class_value_dict = project_details.class_value_dict
        # Get all images uploaded for a project.
        image_infos = dbh.get_images(project_id)
        object_classes = dbh.get_object_classes(project_id)
        class_map = create_class_map(class_value_dict, object_classes)
        # mask_urls = []
        image_voc_urls = []
        storage = UFECLAnnotatorBucket()
        export_folder_name = uuid.uuid4().hex
        for image_info in image_infos:
            image_id = image_info['imageId']
            image_url = image_info['imageUrl']
            image_width = image_info['imageWidth']
            image_height = image_info['imageHeight']
            blob_name = extract_filename_from_url(image_url)
            # Get polygons that have been annotated.
            annotated_polygons = dbh.get_annotated_polygons(image_id)
            if len(annotated_polygons) > 0:
                bbox_infos = []
                for polygon in annotated_polygons:
                    bbox_info = dict()
                    # class_value = class_value_dict[polygon['classId']]
                    class_id = polygon['classId']
                    class_value = get_class_value(class_value_dict, polygon['classId'])
                    bbox_info['class_value'] = class_value
                    # polygon_info['points'] = polygon['points']
                    class_name = get_class_name_by_id(object_classes, class_id)
                    bbox_info['class_name'] = class_name
                    bbox_info['bbox'] = utils.get_bbox_from_polygon(polygon['points'])
                    bbox_infos.append(bbox_info)
                # Convert polygons to mask.
                voc = utils.write_pascal_voc('images', blob_name, bbox_infos, (image_width, image_height, 3))
                # mask = utils.polygons_to_mask(bbox_infos, (image_width, image_height, 3))
                # Convert multiclass mask to rgb representation.
                # rgb_mask = utils.mask_to_rgb(mask, class_map)
                # Convert image to an io stream that can be uploaded s3.
                # mask_blob = convert_np_image_to_io(mask)
                # rgb_mask_blob = convert_np_image_to_io(rgb_mask)
                # Save the masks to S3.
                # voc_url = storage.save(f'exports/mask/{export_folder_name}/{blob_name}.xml', mask_blob)
                voc_url = storage.save_to_exported_voc_folder(blob_name, voc)
                # rgb_mask_url = storage.save(f'exports/rgb/{export_folder_name}/{blob_name}.png', rgb_mask_blob)
                image_voc_urls.append({'image_url': image_url, 'voc_url': voc_url})
        if len(image_voc_urls) > 0:
            # Create a zip file to store exported data.
            zip_buffer = export_images_to_zip(image_voc_urls)
            # Save the zip file in s3 bucket.
            zip_url = storage.save(f'exports/zip/{export_folder_name}/{project_name.replace(" ", "").lower()}.zip'
                                   , zip_buffer)
            # Save export operation in db.
            export_id = dbh.create_export_details(project_id, zip_url).export_id
            for image_voc_url in image_voc_urls:
                mask_url = image_voc_url['voc_url']
                # rgb_mask_url = image_voc_url['rgb_mask_url']
                dbh.save_exported_data(export_id, mask_url)
            return ok(zip_url)
        return ok(None)
