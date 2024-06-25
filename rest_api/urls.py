from django.urls import path

from . import views
from .controllers.login_controller import LoginController
from .utils.load_controllers import load_controllers

# urlpatterns = [
#     path('login', LoginController.as_view())
# ]

urlpatterns = load_controllers()
