from django.urls import path

from django.conf import settings
from . import views
from django.conf.urls.static import static
from .controllers.login_controller import LoginController
from .utils.load_controllers import load_controllers

# urlpatterns = [
#     path('login', LoginController.as_view())
# ]

urlpatterns = [
    path('download/<str:filename>/', views.download_file, name='download_file'),
]

urlpatterns += load_controllers()

if settings.DEBUG:
    urlpatterns += static('/downloads/', document_root=settings.DOWNLOADS_DIR)
