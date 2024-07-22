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
