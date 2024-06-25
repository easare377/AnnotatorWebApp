# utils.py or responses.py
from django.http import JsonResponse


class HttpResponseObject:
    def __init__(self, status_code, message='', data=None, errors=None):
        self.status_code = status_code
        self.message = message
        self.data = data or {}
        self.errors = errors or []

    def to_response(self):
        response_content = {
            'message': self.message,
            'data': self.data,
            'errors': self.errors
        }
        return JsonResponse(response_content, status=self.status_code)
