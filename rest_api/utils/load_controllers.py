# utils/load_controllers.py

import importlib
import inspect
import os
from django.urls import path
from django.conf import settings
from rest_api.controller import Controller


# def get_controllers_from_module(module):
#     controllers = []
#     for name, obj in inspect.getmembers(module):
#         if inspect.isclass(obj) and issubclass(obj, Controller) and obj != Controller:
#             controllers.append(obj)
#     return controllers

def get_controllers_from_module(module):
    controllers = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, Controller) and obj != Controller:
            if hasattr(obj, '_route'):
                controllers.append((obj._route, obj))
            else:
                # Default route name based on the class name
                route_name = obj.__name__.replace('Controller', '').lower()
                controllers.append((route_name, obj))
    return controllers


def load_controllers():
    controllers_dir = os.path.join(settings.BASE_DIR, 'rest_api', 'controllers')
    urlpatterns = []

    for filename in os.listdir(controllers_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f'rest_api.controllers.{filename[:-3]}'
            module = importlib.import_module(module_name)
            controllers = get_controllers_from_module(module)

            for route, controller in controllers:
                urlpatterns.append(path(route, controller.as_view()))

    return urlpatterns
