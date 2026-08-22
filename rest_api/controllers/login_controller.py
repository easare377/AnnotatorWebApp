from ..controller import *
from ..decorators.route import route
from ..objects.login_info import LoginInfo


# class LoginInfo:
#     def __init__(self, username, password):
#         self.username = username
#         self.password = password


@route('login')
class LoginController(Controller):
    def process_post_request(self, login_info: LoginInfo):
        ok(login_info)
        pass
