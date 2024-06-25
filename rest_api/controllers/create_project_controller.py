from abc import ABC
from ..controller import Controller, ok, bad_request
from ..decorators.route import route


@route('project')
class CreateProjectController(Controller, ABC):

    def process_post_request(self, request_object):
        project_name = request_object['projectName']

        return bad_request('Invalid Json')
        return ok(request_object)
