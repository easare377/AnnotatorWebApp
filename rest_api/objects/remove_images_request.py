from dataclasses import dataclass


@dataclass
class RemoveImagesRequest:
    image_ids: list[str]
