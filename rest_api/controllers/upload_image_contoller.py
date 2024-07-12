from ..controller import Controller
from ..decorators.route import route
from ..controller import Controller, ok, bad_request
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
# from ..models import UserInfo, ImageUpload
from ..forms import ImageUploadForm


@route('uploadimage')
class UploadImage(Controller):
    def post(self, request, *args, **kwargs):

        # form = ImageUploadForm(request.POST, request.FILES)
        # if form.is_valid():
        #     form.save()
        #     return JsonResponse({'message': 'Image uploaded successfully'}, status=201)
        # else:
        #     return JsonResponse({'errors': form.errors}, status=400)
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_instance = form.save()
            image_url = image_instance.image.url
            return JsonResponse({'message': 'Image uploaded successfully', 'url': image_url}, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    def process_post_request(self, request_object):
        # val = request_object['image']
        # file = request.FILES['file']
        # file_name = file.name
        # file_type = file.content_type

        return ok("done")

    def process_put_request(self, request_object):
        pass

    def process_get_request(self, request_object):
        pass

    def process_delete_request(self, request_object):
        pass
