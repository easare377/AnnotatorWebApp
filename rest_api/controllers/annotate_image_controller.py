
from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh


@route('projects/data/annotate-image')
class AnnotateImageController(Controller):

    def process_post_request(self, request_object):
        object_class_infos = request_object.object_classes
        dbh.save_or_update_object_classes(object_class_infos)
        return ok('done')
