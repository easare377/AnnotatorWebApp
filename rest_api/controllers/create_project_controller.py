from abc import ABC
from ..controller import *
from rest_api import dbhelper as dbh
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
        created_project = dbh.create_project(project_info)
        project = created_project
        projects = dbh.get_projects()
        # resp = {'project_id': project_id, 'projects': projects}
        return ok(projects)
