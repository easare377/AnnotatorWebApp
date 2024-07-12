from abc import ABC, abstractmethod
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from rest_framework import status
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .http_response.http_response_object import HttpResponseObject
from .request_object import dict_to_object
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse
import json


def authenticate_request(request):
    return True


def ok(data=None):
    return HttpResponseObject(200, body=data)


def bad_request(message=None):
    return HttpResponseObject(400, errors=message)


@method_decorator(csrf_exempt, name='dispatch')
class Controller(View, ABC):

    def post(self, request, *args, **kwargs):
        try:
            # Deserialize the JSON body of the request
            request_json = request.body.decode('utf-8')
            request_dict = json.loads(request_json)
            request_object = dict_to_object(request_dict)
            if not authenticate_request(request_object):
                return JsonResponse({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            response = self.process_post_request(request_object)
            # Return a successful response
            return response.to_response()

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid Data'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the exception (optional)
            print(f'Error: {e}')
            return JsonResponse({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @abstractmethod
    def process_post_request(self, request_object):
        pass
