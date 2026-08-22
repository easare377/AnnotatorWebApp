from abc import ABC, abstractmethod
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import json
from typing import get_type_hints, Type, Any
# from request_object import *
from rest_api import request_object as ro
from rest_api.utils import utils as utils
from .http_response_object import *


# Utility functions

def authenticate_request(request) -> bool:
    """
    Placeholder function to authenticate the request.
    Returns True for all requests.
    """
    return True


def ok(data=None) -> HttpResponseObject:
    """
    Returns an HttpResponseObject with status 200 (OK) and optional data.
    """
    return HttpResponseObject(200, body=data)


def bad_request(message=None) -> HttpResponseObject:
    """
    Returns an HttpResponseObject with status 400 (Bad Request) and optional error message.
    """
    return HttpResponseObject(400, errors=message)


def json_request(func):
    """
    Decorator to mark a request handler as accepting JSON requests.
    """
    func._is_json_request = True
    return func


def multipart_request(func):
    """
    Decorator to mark a request handler as accepting multipart/form-data requests.
    """
    func._is_multipart_request = True
    return func


def handle_json_request(request) -> dict:
    """
    Handles JSON requests by decoding the request body into a dictionary.
    """
    request_json = request.body.decode('utf-8')
    request_dict = json.loads(request_json)
    return request_dict


def handle_multipart_request(request) -> dict:
    """
    Handles multipart/form-data requests by collecting files and form data into a dictionary.
    """
    if not request.FILES and not request.POST:
        raise ValueError('No files or data provided')
    files_dict = {key: value for key, value in request.FILES.items()}
    post_dict = {key: json.loads(value) if is_json(value) else value for key, value in request.POST.items()}
    request_dict = {**files_dict, **post_dict}
    return request_dict


def is_json(value: str) -> bool:
    """
    Checks if a given string value is a valid JSON.
    """
    try:
        json.loads(value)
    except ValueError:
        return False
    return True


# def dict_to_object(data: dict, cls: Type[Any]) -> Any:
#     """
#     Converts a dictionary to an instance of the given class type.
#     Raises an exception if there are missing or extra fields.
#     """
#     if not isinstance(data, dict):
#         raise ValueError('Data must be a dictionary')
#
#     cls_fields = set(cls.__annotations__.keys())
#     data_fields = set(data.keys())
#
#     missing_fields = cls_fields - data_fields
#     extra_fields = data_fields - cls_fields
#
#     if missing_fields or extra_fields:
#         raise ValueError(f"Fields mismatch: Missing fields: {missing_fields}, Extra fields: {extra_fields}")
#
#     return cls(**data)


# Abstract base controller class

@method_decorator(csrf_exempt, name='dispatch')
class Controller(View, ABC):
    """
    Abstract base controller class to handle common request processing logic.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests by deserializing the request body and invoking the process_post_request method.
        """
        try:
            if 'multipart/form-data' in request.content_type:
                request_dict = handle_multipart_request(request)
            else:
                request_dict = handle_json_request(request)
            # convert request dictionary from any format to dictionary
            # with snake_case keys.
            request_dict = utils.convert_dict_to_snake_dict(request_dict)
            request_object = self.get_request_object(request_dict)

            if not authenticate_request(request_object):
                return JsonResponse({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            response = self.process_post_request(request_object)
            return response.to_response()

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as ve:
            return JsonResponse({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_request_object(self, request_dict: dict) -> Any:
        """
        Converts the request dictionary to the expected class type based on type hints.
        """
        hints = get_type_hints(self.process_post_request)
        if hints:
            first_key = next(iter(hints))
            request_cls = hints[first_key]
            return utils.dict_to_object(request_dict, request_cls)
        return ro.dict_to_object(request_dict)

    @abstractmethod
    def process_post_request(self, request_object: Any) -> HttpResponseObject:
        """
        Abstract method to be implemented by subclasses to process POST requests.
        """
        pass
