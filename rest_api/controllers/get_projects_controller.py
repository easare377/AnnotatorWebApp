from ..controller import *
from ..decorators.route import route


@route("projects")
class CreateProjectController(Controller):
    def process_post_request(self, request_object):
        resp = [{'projectId': '1234',
                 'name': 'Project 1',
                 'description': 'Project Description',
                 'dateCreated': '2020-02-02 13:30:23'}, "YYYY-MM-DD HH:mm:ss.SSS"
                {'projectId': '5678',
                 'name': 'Waterbodies',
                 'description': 'Project Description',
                 'dateCreated': '2024-02-02'},
                {'projectId': '56783',
                 'name': 'Building',
                 'description': 'Project Description',
                 'dateCreated': '2025-02-02'}
                ]
        return ok(resp)
