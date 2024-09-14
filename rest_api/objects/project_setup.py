from dataclasses import dataclass
from ..objects.object_class import ObjectClass


@dataclass
class ProjectSetup:
    annotation_type: str
    object_classes: ObjectClass
