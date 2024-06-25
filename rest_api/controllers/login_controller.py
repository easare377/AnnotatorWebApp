from ..controller import Controller
from ..decorators.route import route


@route('login')
class LoginController(Controller):

    def process_post_request(self, request_object):
        email = request_object.email #.body['email']
        password = request_object.password
        return badrequest()
        # return 'Hello World!'
