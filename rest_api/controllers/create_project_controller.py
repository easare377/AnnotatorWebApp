from abc import ABC
from ..controller import *
from ..decorators.route import route
from ..models import Projects
from ..dbhelper import *


@route('create-project')
class CreateProjectController(Controller):
    def process_post_request(self, request_object):
        # project_name = request_object.name
        # project_description = request_object.description
        # project_setup = request_object.project_setup
        # annotation_type = project_setup.annotation_type
        #
        # project_name = request_object['projectName']
        project_info = request_object
        create_project(project_info)
        projects = get_projects()
        return ok(projects)
