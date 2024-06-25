from ..controller import Controller


class LoginController(Controller):

    def process_post_request(self, request_object):
        return self.ok('Hi World!')
        # return 'Hello World!'
