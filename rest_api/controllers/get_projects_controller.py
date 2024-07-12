from ..controller import *
from ..decorators.route import route
from ..dbhelper import *


@route("projects")
class ProjectsController(Controller):
    def process_post_request(self, request_object):
        # resp = [{'projectId': '092cfa2c-371d-516e-8eb7-776931146f90',
        #          'name': 'Project 1',
        #          'description': 'Project Description',
        #          'dateCreated': '2020-02-02 13:30:23'},
        #         {'projectId': '092cfa2c-471d-516e-8eb7-776931146fd6',
        #          'name': 'Waterbodies',
        #          'description': 'Project Description',
        #          'dateCreated': '2024-02-02'},
        #         {'projectId': '56783',
        #          'name': 'Building',
        #          'description': 'Project Description',
        #          'dateCreated': '2025-02-02'}
        #         ]
        projects = get_projects()
        return ok(projects)
