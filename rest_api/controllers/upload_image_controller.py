
from ..controller import *
from ..decorators.route import route
from ..dbhelper import *

@route('upload_image')
class UploadImageController(Controller):
    def process_post_request(self, request_object):
        image = request_object.image
        url = s3_cli.bucket.upload(image)
        save_info(url)
        pass
