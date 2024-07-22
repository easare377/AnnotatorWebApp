from abc import ABC, abstractmethod
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import json
# from request_object import *
from rest_api import request_object as ro
from .http_response_object import *


def authenticate_request(request):
    return True


def ok(data=None):
    return HttpResponseObject(200, body=data)


def bad_request(message=None):
    return HttpResponseObject(400, errors=message)


def json_request(func):
    func._is_json_request = True
    return func


def multipart_request(func):
    func._is_multipart_request = True
    return func


def handle_json_request(request):
    request_json = request.body.decode('utf-8')
    request_dict = json.loads(request_json)
    return ro.dict_to_object(request_dict)


def handle_multipart_request(request):
    if not request.FILES and not request.POST:
        raise ValueError('No files or data provided')
    # Collect all files from the request
    files_dict = {key: value for key, value in request.FILES.items()}
    # Collect all POST data from the request
    post_dict = {key: json.loads(value) if is_json(value) else value for key, value in request.POST.items()}
    # Combine both dictionaries
    request_dict = {**files_dict, **post_dict}
    request_object = ro.dict_to_object(request_dict)
    return request_object


def is_json(value):
    try:
        json.loads(value)
    except ValueError:
        return False
    return True


@method_decorator(csrf_exempt, name='dispatch')
class Controller(View, ABC):

    def post(self, request, *args, **kwargs):
        try:
            if 'multipart/form-data' in request.content_type:
                # Handle multipart request
                request_object = handle_multipart_request(request)
            else:
                # Default to JSON request if not multipart
                request_object = handle_json_request(request)

            if not authenticate_request(request_object):
                return JsonResponse({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            response = self.process_post_request(request_object)
            return response.to_response()

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid Data'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @abstractmethod
    def process_post_request(self, request_object):
        pass
