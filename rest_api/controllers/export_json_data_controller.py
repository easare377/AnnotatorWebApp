from ..controller import *
from ..decorators.route import route
from ..objects.export_project_details import ExportProjectDetails
from ..s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket
from rest_api import dbhelper as dbh
import uuid
from rest_api.utils import utils
import json
import io
from urllib.parse import urlparse
import os
import requests
import zipfile


def convert_polygon(polygon):
    # Initialize an empty list to store the converted polygon
    converted_polygon = []
    # Iterate over each list of points in the polygon
    converted_sub_polygon = []
    # Convert each point dictionary {x, y} to a list [x, y]
    for point in polygon:
        converted_polygon.append([point['x'], point['y']])
    # Add the converted sub-polygon to the final result
    return converted_polygon


def export_json_to_zip(json_urls):
    # Create an in-memory byte stream to store the ZIP file
    zip_buffer = io.BytesIO()
    # count = 1
    # Initialize the ZipFile object
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for image_json_url in json_urls:
            original_filename = image_json_url['original_filename']
            json_url = image_json_url['json_url']
            # Download the mask
            response = requests.get(json_url)
            if response.status_code == 200:
                json_data = response.content
                # Store the mask in the "mask" folder in the ZIP
                zip_file.writestr(f'{original_filename}.json', json_data)
            else:
                print(f"Failed to download image from {json_url}")
    # Return the in-memory ZIP file
    zip_buffer.seek(0)
    return zip_buffer


def get_class_name_by_id(object_class_list, classId):
    """
    Retrieves the class name from the object class list using the classId.

    Parameters:
    - object_class_list (list): A list of dictionaries containing object class details.
    - classId (str): The unique identifier of the object class.

    Returns:
    - str: The class name associated with the classId.
    """
    for obj_class in object_class_list:
        if obj_class['classId'] == str(classId):
            return obj_class['className']

    # If classId is not found, raise an exception or return a default message
    raise ValueError(f"Class with ID {classId} not found.")


@route('projects/data/export/json')
class ExportJsonDataController(Controller):

    def process_post_request(self, project_details: ExportProjectDetails):
        project_id = project_details.project_id
        project = dbh.get_project_details(project_id)
        project_name = project['name']
        class_value_dict = project_details.class_value_dict
        # Get all images uploaded for a project.
        image_infos = dbh.get_images(project_id)
        object_classes = dbh.get_object_classes(project_id)
        # object_class = dbh.get_object_class()
        export_folder_name = uuid.uuid4().hex
        storage = UFECLAnnotatorBucket()
        json_infos = []
        for image_info in image_infos:
            image_id = image_info['imageId']
            image_url = image_info['imageUrl']
            original_filename = image_info['originalFilename']
            image_width = image_info['imageWidth']
            image_height = image_info['imageHeight']
            blob_name = utils.extract_filename_from_url(image_url)
            # Get polygons that have been annotated.
            annotated_polygons = dbh.get_annotated_polygons(image_id)
            polygon_infos = []
            for polygon in annotated_polygons:
                points = convert_polygon(polygon['points'])
                class_id = polygon['classId']
                class_name = get_class_name_by_id(object_classes, class_id)
                polygon_info = {'className': class_name, 'points': points}
                polygon_infos.append(polygon_info)
            # Convert the object to a JSON string
            json_str = json.dumps(polygon_infos)
            json_url = storage.save_to_exported_json_folder(blob_name, json_str)
            json_infos.append({'json_url': json_url, 'original_filename': original_filename})
        if len(json_infos) > 0:
            # Create a zip file to store exported data.
            zip_buffer = export_json_to_zip(json_infos)
            # Save the zip file in s3 bucket.
            zip_url = storage.save(f'exports/zip/{export_folder_name}/{project_name.replace(" ", "").lower()}.zip'
                                   , zip_buffer)
            # Save export operation in db.
            export_id = dbh.create_export_details(project_id, zip_url).export_id
            for json_info in json_infos:
                json_url = json_info['json_url']
                dbh.save_exported_data(export_id, json_url)
            return ok(zip_url)
        return ok(None)
