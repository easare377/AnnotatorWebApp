from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh


@route('delete-project')
class DeleteProjectController(Controller):

    def process_post_request(self, request_object):
        project_id = request_object.project_id
        dbh.delete_project(project_id)
        return ok('done')


