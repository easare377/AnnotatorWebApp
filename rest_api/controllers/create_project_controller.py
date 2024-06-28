from abc import ABC
from ..controller import *
from ..decorators.route import route
from ..models import Projects
from ..dbhelper import *

@route('project')
class CreateProjectController(Controller):
    def process_post_request(self, request_object):
        project_info = request_object['project_info']
        image_info = request_object['image_info']
        project_name = request_object['projectName']
        create_project(project_info, 'Desc')
        return bad_request('Invalid Json')
        return ok(request_object)
