from dataclasses import dataclass


@dataclass
class ExportProjectDetails:
    project_id: str
    class_value_dict: list
