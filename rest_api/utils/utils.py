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


def validate_points(points):
    """
    Validate that the points are in the correct format.

    Parameters:
    - points: The points to validate.

    Raises:
    - ValidationError: If the points are not in the correct format.
    """
    if not isinstance(points, list):
        return False

    for point in points:
        if not isinstance(point, dict):
            return False
            # raise ValidationError("Each point must be a dictionary.")
        if 'x' not in point or 'y' not in point:
            return False
            # raise ValidationError("Each point must have 'x' and 'y' keys.")
        if not isinstance(point['x'], (int, float)) or not isinstance(point['y'], (int, float)):
            return False
            # raise ValidationError("'x' and 'y' must be numeric values.")
    return True
