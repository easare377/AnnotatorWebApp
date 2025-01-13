from ..controller import *
from ..decorators.route import route

# from ..dbhelper import *
from rest_api import dbhelper as dbh
from PIL import Image
from django.core.files.uploadedfile import UploadedFile
from ..utils.image_details import *
import uuid
import boto3
from django.core.files.storage import default_storage
from ..s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket
from io import BytesIO
from rest_api import stopwatch
import requests
import base64
from ..models import (
    Projects,
    ImageInfo,
    ProjectSetup,
    ObjectClass,
    AnnotationType,
    ImageType,
)


def convert_to_png(pil_image: Image, compress_level: int = 9) -> BytesIO:
    """
    Convert a PIL image to PNG format with specified compression.
    Parameters:
    - pil_image: The PIL image to convert.
    - compress_level: The level of compression for the PNG image (0-9). Higher values mean more compression.
    Returns:
    - A BytesIO object containing the PNG image.
    """
    # Ensure compress_level is between 0 and 9
    compress_level = max(0, min(compress_level, 9))
    # Convert the image to PNG format with compression
    png_image = BytesIO()
    pil_image.save(png_image, format="PNG", compress_level=compress_level)
    png_image.seek(0)
    return png_image


def convert_to_jpeg(pil_image: Image, quality: int = 85) -> BytesIO:
    """
    Convert a PIL image to JPEG format with specified quality.

    Parameters:
    - pil_image: The PIL image to convert.
    - quality: The quality level for the JPEG image (1-100). Higher values mean better quality and less compression.

    Returns:
    - A BytesIO object containing the JPEG image.
    """
    # Ensure quality is between 1 and 100
    quality = max(1, min(quality, 100))
    # Convert the image to JPEG format with the specified quality
    jpg_image = BytesIO()
    pil_image.save(jpg_image, format="JPEG", quality=quality)
    jpg_image.seek(0)
    return jpg_image


# def get_image_details(image: UploadedFile) -> ImageDetails:
#     """
#     Extract information from an image and return an object with properties file_name, width, and height.
#
#     :param image: UploadedFile - The image file
#     :return: ImageDetails - An object containing the image details
#     """
#     with Image.open(image) as img:
#         width, height = img.size
#         file_name = image.name
#
#     return ImageDetails(file_name, width, height)

# def get_image_size(pil_image: Image):
#     """
#     Extract information from an image and return an object with properties file_name, width, and height.
#
#     :param image: UploadedFile - The image file
#     :return: ImageDetails - An object containing the image details
#     """
#     with Image.open(image) as img:
#         width, height = pil_image.size
#         file_name = image.name
#
#     return ImageDetails(file_name, width, height)


# @route('projects/data/upload-image')
# class UploadImageController(Controller):
#     @multipart_request
#     def process_post_request(self, request_object):
#         uploaded_image = request_object.image
#         project_id = request_object.image_details.project_id
#         with Image.open(uploaded_image) as img:
#             width, height = img.size
#             # Convert uploaded image to png.
#             png_image = convert_to_png(img)
#             jpg_image = convert_to_jpeg(img)
#         image_details = ImageDetails(uploaded_image.name, width, height)
#         # Save the image to S3
#         storage = UFECLAnnotatorBucket()
#         image_file_name = str(uuid.uuid4())
#         png_image_url = storage.save(f'images/png/{image_file_name}.png', png_image)
#         jpg_image_url = storage.save(f'images/jpeg/{image_file_name}.jpg', jpg_image)
#         # Save the uploaded image details to the db.
#         dbh.save_image_info(project_id, png_image_url, jpg_image_url, image_details)
#         image_infos = dbh.get_images(project_id)
#         return ok(data=image_infos)


@route("projects/data/upload-image")
class UploadImageController(Controller):
    @multipart_request
    def process_post_request(self, request_object):

        uploaded_image = request_object.image
        project_id = request_object.image_details.project_id
        print(request_object)

        print(request_object.image)
        print(request_object.image_details.project_id)

        # Read and encode image to base64
        image_data = base64.b64encode(uploaded_image.read()).decode("utf-8")
        # print(image_data)

        # Prepare payload to send to Lambda through API Gateway
        payload = {
            "image_details": {"project_id": project_id},
            "image": str(image_data),
        }

        # Call the Lambda function through API Gateway
        lambda_url = (
            "https://ksdxgew5kf.execute-api.us-east-2.amazonaws.com/test/upload"
        )
        headers = {"Content-Type": "application/json"}
        response = requests.post(lambda_url, json=payload, headers=headers)
        print(response)
        if response.status_code == 200:
            lambda_response = response.json()

            # Extract the URLs and image details from Lambda response
            png_image_url = lambda_response["png_image_url"]
            jpg_image_url = lambda_response["jpg_image_url"]
            thumbnail_url = lambda_response["thumnail_url"]
            image_details = lambda_response["image_details"]
            print(f"Lambda Response: {response.json()}")

            # Save the uploaded image details to the database
            if not Projects.objects.filter(project_id=project_id).exists():
                raise ValueError(f"Project with ID {project_id} does not exist.")

            dbh.save_image_info(
                project_id, png_image_url, jpg_image_url, thumbnail_url, image_details
            )

            # # Retrieve all image information for the project
            image_infos = dbh.get_images(project_id)

            # Return response with the image details
            return ok(data=image_infos)
