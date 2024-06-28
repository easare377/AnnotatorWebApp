from .models import *
import uuid


def add_annotation_type_if_not_exist():
    # Define a namespace and a name (string) to generate the UUID
    namespace = uuid.NAMESPACE_DNS
    polygon_name = "POLYGON"
    bbox_name = "BBOX"
    AnnotationType(annotation_id=uuid.uuid5(namespace, polygon_name), annotation_type='POLYGON').save()
    AnnotationType(annotation_id=uuid.uuid5(namespace, bbox_name), annotation_type='BBOX').save()
#
# # def create_project(self, project_info, image_info):
# #     project_name = project_info['name']
# #     project_description = project_info['description']
# #     projects = Projects(project_name=project_name, project_description)
# #     projects.save()
# #     image_url = image_info['url']
#
# # image_info = ImageInfo()
#
# # def update_project(self, project_name, description=None):
# #     projects = Projects()
# #     projects.
#
# def get_projects_info(project_id):
#     projects = Projects.objects.all()
#     return projects
