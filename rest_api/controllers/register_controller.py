from ..controller import Controller


class RegisterController(Controller):
    def process_post_request(self, request_object):
        val = request_object['key']
        return self.ok(val)