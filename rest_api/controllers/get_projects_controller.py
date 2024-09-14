from ..controller import *
from ..decorators.route import route
from ..dbhelper import *


@route("projects")
class ProjectsController(Controller):
    def process_post_request(self, request_object):
        projects = get_projects()
        return ok(projects)
