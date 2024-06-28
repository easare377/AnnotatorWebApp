from django.apps import AppConfig


class RestApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rest_api"

    def ready(self):
        from .dbhelper import add_annotation_type_if_not_exist
        add_annotation_type_if_not_exist()
