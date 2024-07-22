# utils.py or responses.py
from django.http import JsonResponse


class HttpResponseObject:
    def __init__(self, status_code, body=None, errors=None):
        self.status_code = status_code
        # self.message = message
        self.body = body or {}
        self.errors = errors or []

    def to_response(self):
        # response_content = {
        #     'message': self.message,
        #     'data': self.data,
        #     'errors': self.errors
        # }
        return JsonResponse(self.body, status=self.status_code, safe=False)
