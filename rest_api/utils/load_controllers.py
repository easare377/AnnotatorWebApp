# utils/load_controllers.py

import importlib
import inspect
import os
from django.urls import path
from django.conf import settings
from rest_api.controller import Controller


def get_controllers_from_module(module):
    controllers = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, Controller) and obj != Controller:
            controllers.append(obj)
    return controllers


def load_controllers():
    controllers_dir = os.path.join(settings.BASE_DIR, 'rest_api', 'controllers')
    urlpatterns = []

    for filename in os.listdir(controllers_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f'rest_api.controllers.{filename[:-3]}'
            module = importlib.import_module(module_name)
            controllers = get_controllers_from_module(module)

            for controller in controllers:
                route_name = controller.__name__.replace('Controller', '').lower()
                urlpatterns.append(path(route_name, controller.as_view()))

    return urlpatterns
