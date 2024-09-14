import re
from typing import Any, Type, List, Union, get_args, get_origin, Dict
from dataclasses import fields, is_dataclass, dataclass
from shapely.geometry import Polygon, Point
from shapely.affinity import affine_transform
import numpy as np
import cv2


def camel_to_snake(name):
    """
    Convert camelCase string to snake_case.
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def underscore_camel_to_snake(name: str) -> str:
    """
    Convert underscore camelCase string to snake_case.
    """
    name = name[1:]  # Removing the leading underscore
    return camel_to_snake(name)


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


def convert_dict_to_snake_dict(entries: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts all keys in the dictionary to snake_case.

    Args:
        entries (Dict[str, Any]): The input dictionary with keys in camelCase or underscoreCamel.

    Returns:
        Dict[str, Any]: A new dictionary with all keys converted to snake_case.
    """

    def convert_key(key: str) -> str:
        if key[0] == '_':
            return underscore_camel_to_snake(key)
        return camel_to_snake(key)

    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            return {convert_key(k): convert(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert(item) for item in value]
        return value

    return {convert_key(k): convert(v) for k, v in entries.items()}


def dict_to_object(data: Union[dict, List[dict]], cls: Type[Any]) -> Any:
    """
    Converts a dictionary or a list of dictionaries to an instance or list of instances of the given class type,
    handling nested dataclasses. Raises an exception if there are missing or extra fields.

    Args:
        data (Union[dict, List[dict]]): The input dictionary or list of dictionaries.
        cls (Type[Any]): The class type to convert the dictionary into.

    Returns:
        Any: An instance or list of instances of the class type.

    Raises:
        ValueError: If there are missing or extra fields.
    """
    if isinstance(data, list):
        # If data is a list, recursively convert each item in the list.
        return [dict_to_object(item, cls) for item in data]

    if not isinstance(data, dict):
        raise ValueError('Data must be a dictionary or a list of dictionaries')

    if not is_dataclass(cls):
        raise ValueError('Class must be a dataclass')

    cls_fields = {field.name: field.type for field in fields(cls)}
    data_fields = set(data.keys())

    missing_fields = cls_fields.keys() - data_fields
    extra_fields = data_fields - cls_fields.keys()

    if missing_fields or extra_fields:
        raise ValueError(f"Fields mismatch: Missing fields: {missing_fields}, Extra fields: {extra_fields}")

    init_kwargs = {}
    for field_name, field_type in cls_fields.items():
        field_value = data[field_name]
        if is_dataclass(field_type):
            field_value = dict_to_object(field_value, field_type)
        elif get_origin(field_type) == list:
            item_type = get_args(field_type)[0]
            if is_dataclass(item_type):
                field_value = [dict_to_object(item, item_type) for item in field_value]
        init_kwargs[field_name] = field_value

    return cls(**init_kwargs)


#
# def polygons_to_mask(polygon_infos, mask_size):
#     mask = np.zeros(mask_size, dtype=np.uint8)
#     width, height = mask_size
#
#     for poly_info in polygon_infos:
#         class_value = poly_info['class_value']
#         points = poly_info['points']
#         # Convert points to shapely Polygon
#         polygon = Polygon([(point['x'], point['y']) for point in points])
#
#         # Get the bounding box of the polygon
#         minx, miny, maxx, maxy = polygon.bounds
#         if minx < 0 or miny < 0 or maxx >= width or maxy >= height:
#             raise ValueError("Polygon points are out of mask bounds")
#
#         # Create an affine transformation matrix to fit the polygon in the mask
#         scale_x = width / (maxx - minx)
#         scale_y = height / (maxy - miny)
#         translate_x = -minx * scale_x
#         translate_y = -miny * scale_y
#         transform = [scale_x, 0, 0, scale_y, translate_x, translate_y]
#
#         # Apply the transformation to the polygon
#         transformed_polygon = affine_transform(polygon, transform)
#
#         # Rasterize the transformed polygon into the mask
#         x, y = np.meshgrid(np.arange(width), np.arange(height))
#         points = np.vstack((x.flatten(), y.flatten())).T
#         mask_polygon = np.array([transformed_polygon.contains(Point(p)) for p in points])
#         mask_polygon = mask_polygon.reshape((height, width))
#         mask[mask_polygon] = class_value
#     return mask


def is_point_in_polygon(x, y, polygon):
    """
    Determine if a point is inside a polygon using the ray-casting algorithm.

    Args:
    - x (int): x-coordinate of the point.
    - y (int): y-coordinate of the point.
    - polygon (list of dicts): List of points defining the polygon.

    Returns:
    - bool: True if the point is inside the polygon, False otherwise.
    """
    num_points = len(polygon)
    j = num_points - 1
    inside = False

    for i in range(num_points):
        xi, yi = polygon[i]['x'], polygon[i]['y']
        xj, yj = polygon[j]['x'], polygon[j]['y']

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside

        j = i

    return inside


# def polygons_to_mask(polygon_infos, image_size):
#     """
#     Convert polygon information to a multiclass segmentation mask.
#
#     Args:
#     - polygon_infos (list of dicts): List of polygons with class values and points.
#     - image_size (tuple): Size of the output mask (height, width).
#
#     Returns:
#     - np.ndarray: Multiclass segmentation mask.
#     """
#     width, height = image_size
#     mask = np.zeros((height, width), dtype=np.uint8)
#
#     for polygon_info in polygon_infos:
#         class_value = polygon_info['class_value']
#         points = polygon_info['points']
#
#         # Calculate the bounding box of the polygon
#         min_x = min(point['x'] for point in points)
#         max_x = max(point['x'] for point in points)
#         min_y = min(point['y'] for point in points)
#         max_y = max(point['y'] for point in points)
#
#         # Clip the bounding box to the image size
#         min_x = max(min_x, 0)
#         max_x = min(max_x, width - 1)
#         min_y = max(min_y, 0)
#         max_y = min(max_y, height - 1)
#
#         # Iterate only within the bounding box
#         for y in range(min_y, max_y + 1):
#             for x in range(min_x, max_x + 1):
#                 if is_point_in_polygon(x, y, points):
#                     mask[y, x] = class_value
#     return mask


def polygons_to_mask(polygon_infos, image_size):
    width, height = image_size
    img = np.zeros([height, width], dtype=np.uint8)
    for polygon_info in polygon_infos:
        class_value = polygon_info['class_value']
        points = polygon_info['points']
        points = [[point['x'], point['y']] for point in points]
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(img, [points], class_value)
    return img


def mask_to_rgb(mask, class_map):
    """
    Converts a segmentation mask into an RGB image based on the class map.

    Args:
        mask (np.ndarray): A 2D numpy array where each value represents a class.
        class_map (list of dict): A list of dictionaries where each dictionary contains:
                                  - 'class_value': The integer value of the class in the mask.
                                  - 'color': A list of three integers representing the RGB color for the class.

    Returns:
        np.ndarray: A 3D numpy array (H, W, 3) representing the RGB image.
    """
    # Create an empty RGB image
    rgb_image = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    # Iterate over the class map and assign colors to corresponding class values
    for entry in class_map:
        class_value = entry['class_value']
        color = entry['color']
        # Create a mask for the current class
        class_mask = (mask == class_value)
        # Assign the RGB color to the corresponding pixels in the output image
        rgb_image[class_mask] = color
    return rgb_image


def hex_to_rgb(hex_color):
    """
    Convert a hex color string to an RGB list.

    Parameters:
        hex_color (str): A string representing a hex color (e.g., "#FFFFFF").

    Returns:
        list: A list of integers representing the RGB color [r, g, b].
    """
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)]
