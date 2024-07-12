from ..controller import Controller
from ..decorators.route import route


@route('login')
class LoginController(Controller):
    def process_post_request(self, request_object):
        pass
