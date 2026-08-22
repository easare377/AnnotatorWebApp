from abc import ABC
from ..controller import *
from rest_api import dbhelper as dbh
from ..decorators.route import route
from ..models import Projects
from ..dbhelper import *
from ..objects.project_info import ProjectInfo


@route('create-project')
class CreateProjectController(Controller):
    def process_post_request(self, project_info: ProjectInfo):
        created_project = dbh.create_project(project_info)
        project = created_project
        projects = dbh.get_projects()
        # resp = {'project_id': project_id, 'projects': projects}
        return ok(projects)
