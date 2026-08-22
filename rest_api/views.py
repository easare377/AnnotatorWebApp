from django.shortcuts import render

# Create your views here.
from django.http import FileResponse, Http404
import os
from django.conf import settings


def download_file(request, filename):
    file_path = os.path.join(settings.DOWNLOADS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    else:
        raise Http404("File not found")
