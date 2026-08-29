from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views
from .controllers.login_controller import LoginController
from .objects.url_paths import USER_DATA_PATH
from .utils.load_controllers import load_controllers


# urlpatterns = [
#     path("login", LoginController.as_view())
# ]

urlpatterns = [
    path("download/<str:filename>/", views.download_file, name="download_file"),
]

urlpatterns += load_controllers()

if settings.DEBUG:
    urlpatterns += static("/downloads/", document_root=settings.DOWNLOADS_DIR)
    urlpatterns += static(
        f"/{USER_DATA_PATH.as_posix()}/",
        document_root=Path(settings.BASE_DIR).joinpath(*USER_DATA_PATH.parts),
    )
    # Preserve URLs already stored before user data moved below /userdata/.
    urlpatterns += static(
        "/uploads/",
        document_root=Path(settings.BASE_DIR) / "uploads",
    )
