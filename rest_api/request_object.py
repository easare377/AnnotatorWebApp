import json
import rest_api.utils.utils as utils


class RequestObject:
    """
    A class to convert dictionary keys to attributes.
    """

    def __init__(self, **entries):
        for key, value in entries.items():
            if key[0] == '_':
                snake_key = utils.underscore_camel_to_snake(key)
            else:
                snake_key = utils.camel_to_snake(key)
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
