import json
import re


def camel_to_snake(name):
    """
    Convert camelCase string to snake_case.
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def underscore_camel_to_snake(name):
    """
    Convert underscore camelCase string to snake_case.
    """
    # Remove leading underscore and convert the remaining string from camelCase to snake_case
    name_without_leading_underscore = name.lstrip('_')
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name_without_leading_underscore)
    snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    return snake_case


class RequestObject:
    """
    A class to convert dictionary keys to attributes.
    """

    def __init__(self, **entries):
        for key, value in entries.items():
            snake_key = underscore_camel_to_snake(key)
            if isinstance(value, dict):
                # Recursively convert sub-dictionaries to RequestObject
                value = dict_to_object(value)
            elif isinstance(value, list):
                # Recursively convert dictionaries within lists to RequestObject
                value = [dict_to_object(item) if isinstance(item, dict) else item for item in value]
            setattr(self, snake_key, value)


def dict_to_object(d):
    """
    Convert a dictionary to a RequestObject instance.
    """
    return RequestObject(**d)
