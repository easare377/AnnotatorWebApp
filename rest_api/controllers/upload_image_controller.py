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

def convert_to_png(pil_image: Image):
    # Convert the image to PNG format
    png_image = BytesIO()
    pil_image.save(png_image, format='PNG')
    png_image.seek(0)
    return png_image


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


@route('projects/data/upload-image')
class UploadImageController(Controller):
    @multipart_request
    def process_post_request(self, request_object):
        uploaded_image = request_object.image
        project_id = request_object.image_details.project_id
        with Image.open(uploaded_image) as img:
            width, height = img.size
            png_image = convert_to_png(img)
        image_details = ImageDetails(uploaded_image.name, width, height)
        # Save the image to S3
        storage = UFECLAnnotatorBucket()
        file_name = storage.save(f'{str(uuid.uuid4())}.png', png_image)
        image_url = storage.url(file_name)
        dbh.save_image_info(project_id, image_url, image_details)
        image_infos = dbh.get_images(project_id)
        return ok(data=image_infos)
