from dataclasses import dataclass

from rest_api.objects.project_setup import ProjectSetup


@dataclass
class ProjectInfo:
    name: str
    description: str
    project_setup: ProjectSetup
