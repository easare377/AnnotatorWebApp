from django.apps import AppConfig

from .objects.storage_directory_handler_factory import (
    get_storage_directory_handler,
)
from .objects.url_paths import STORAGE_DIRECTORIES


def initialize_storage_directories() -> None:
    """Initialize the configured backend's stable storage directories."""
    handler = get_storage_directory_handler()
    handler.create_directories(STORAGE_DIRECTORIES)


class RestApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rest_api"

    def ready(self):
        from .dbhelper import add_annotation_type_if_not_exist

        initialize_storage_directories()
        add_annotation_type_if_not_exist()
