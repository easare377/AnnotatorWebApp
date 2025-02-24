from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh


@route("projects/delete-image")
class AnnotateImageController(Controller):

    def process_post_request(self, request_object):
        project_id = request_object.project_id
        image_id = request_object.image_id
        print(request_object)
        print("hi")

        dbh.delete_image(project_id, image_id)

        return ok("done")
