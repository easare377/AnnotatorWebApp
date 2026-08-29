from rest_api.objects.model_config import ModelConfig
import os

from ..controller import *
from ..decorators.route import route
from ..interfaces.i_generate_polygons_handler import IGeneratePolygonsHandler
from ..polygon_generation.lambda_generate_polygons_handler import (
    LambdaGeneratePolygonsHandler,
)
from ..polygon_generation.local_generate_polygons_handler import (
    LocalGeneratePolygonsHandler,
)
from ..polygon_generation.runpod_generate_polygons_handler import (
    RunPodGeneratePolygonsHandler,
)

# from rest_api.utils import sam as sam
from rest_api import dbhelper as dbh
from ..utils.runpod_polygon_info import RunPodPolygonInfo
from rest_api import stopwatch
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon as ShapelyPolygon
from shapely.ops import unary_union


MIN_POLYGON_AREA = 1.0


def convert_prompts_to_sam_payload(prompts):
    if not prompts:
        return {
            "positive_points": [],
            "negative_points": [],
            "bbox": None,
        }

    def get_value(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def point_to_xy(point):
        return [
            get_value(point, "x"),
            get_value(point, "y"),
        ]

    def bbox_to_xyxy(bbox):
        if not bbox:
            return None

        return [
            get_value(bbox, "x_min"),
            get_value(bbox, "y_min"),
            get_value(bbox, "x_max"),
            get_value(bbox, "y_max"),
        ]

    positive_points = get_value(prompts, "positive_points", [])
    negative_points = get_value(prompts, "negative_points", [])
    bbox = get_value(prompts, "bbox")

    return {
        "positive_points": [point_to_xy(point) for point in positive_points],
        "negative_points": [point_to_xy(point) for point in negative_points],
        "bbox": bbox_to_xyxy(bbox),
    }


def get_worker_polygon_value(polygon, *keys, default=None):
    for key in keys:
        if isinstance(polygon, dict) and key in polygon:
            return polygon[key]
        if hasattr(polygon, key):
            return getattr(polygon, key)
    return default


def convert_worker_point(point):
    if isinstance(point, dict):
        return {"x": point.get("x"), "y": point.get("y")}
    return {"x": point[0], "y": point[1]}


def convert_worker_points(points):
    return [convert_worker_point(point) for point in points]


def convert_worker_polygon_to_polygon_info(polygon):
    if isinstance(polygon, dict):
        points = get_worker_polygon_value(polygon, "points", default=[])
        inner_polygons = get_worker_polygon_value(
            polygon,
            "inner_polygons",
            "innerPolygons",
            "holes",
            default=[],
        )
    else:
        points = polygon
        inner_polygons = []

    converted_inner_polygons = [
        convert_worker_points(get_worker_polygon_value(inner_polygon, "points", default=inner_polygon))
        for inner_polygon in inner_polygons
    ]
    return RunPodPolygonInfo(
        1.0,
        1.0,
        convert_worker_points(points),
        converted_inner_polygons,
    )


def convert_polygon_point_to_xy(point):
    if isinstance(point, dict):
        return (float(point.get("x")), float(point.get("y")))
    return (float(point[0]), float(point[1]))


def convert_polygon_points_to_xy(points):
    return [convert_polygon_point_to_xy(point) for point in points]


def get_polygon_inner_polygons(polygon_info):
    return get_worker_polygon_value(
        polygon_info,
        "inner_polygons",
        "innerPolygons",
        "holes",
        default=[],
    )


def polygon_info_to_geometry(polygon_info):
    points = get_worker_polygon_value(polygon_info, "points", default=[])
    if len(points) < 3:
        return None

    inner_polygons = []
    for inner_polygon in get_polygon_inner_polygons(polygon_info):
        inner_points = get_worker_polygon_value(
            inner_polygon,
            "points",
            default=inner_polygon,
        )
        if len(inner_points) >= 3:
            inner_polygons.append(convert_polygon_points_to_xy(inner_points))

    try:
        geometry = ShapelyPolygon(
            convert_polygon_points_to_xy(points),
            inner_polygons,
        )
    except (TypeError, ValueError):
        return None

    if not geometry.is_valid:
        geometry = geometry.buffer(0)

    if geometry.is_empty or geometry.area <= MIN_POLYGON_AREA:
        return None

    return geometry


def normalize_polygon_geometry(geometry):
    if not geometry or geometry.is_empty:
        return []
    if isinstance(geometry, ShapelyPolygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        polygons = []
        for item in geometry.geoms:
            polygons.extend(normalize_polygon_geometry(item))
        return polygons
    return []


def clean_coordinate(value):
    rounded_value = round(float(value), 3)
    if abs(rounded_value - round(rounded_value)) < 0.001:
        return int(round(rounded_value))
    return rounded_value


def coordinates_to_points(coordinates):
    coordinate_list = list(coordinates)
    if len(coordinate_list) > 1 and coordinate_list[0] == coordinate_list[-1]:
        coordinate_list = coordinate_list[:-1]
    return [
        {
            "x": clean_coordinate(x),
            "y": clean_coordinate(y),
        }
        for x, y, *_ in coordinate_list
    ]


def geometry_to_polygon_infos(geometry, source_polygon_info):
    polygon_infos = []
    stability_score = get_worker_polygon_value(
        source_polygon_info,
        "stability_score",
        "stabilityScore",
        default=1.0,
    )
    predicted_iou = get_worker_polygon_value(
        source_polygon_info,
        "predicted_iou",
        "predictedIoU",
        default=1.0,
    )

    for polygon in normalize_polygon_geometry(geometry):
        if polygon.area <= MIN_POLYGON_AREA:
            continue

        points = coordinates_to_points(polygon.exterior.coords)
        if len(points) < 3:
            continue

        inner_polygons = []
        for interior in polygon.interiors:
            inner_polygon_points = coordinates_to_points(interior.coords)
            if len(inner_polygon_points) >= 3:
                inner_polygons.append(inner_polygon_points)

        polygon_infos.append(
            RunPodPolygonInfo(
                stability_score,
                predicted_iou,
                points,
                inner_polygons,
            )
        )

    return polygon_infos


def remove_annotated_polygon_overlaps(polygon_infos, annotated_polygon_infos):
    if not annotated_polygon_infos:
        return polygon_infos

    annotated_geometries = [
        geometry
        for geometry in (
            polygon_info_to_geometry(polygon_info)
            for polygon_info in annotated_polygon_infos
        )
        if geometry is not None
    ]
    if not annotated_geometries:
        return polygon_infos

    annotated_union = unary_union(annotated_geometries)
    adjusted_polygon_infos = []
    for polygon_info in polygon_infos:
        geometry = polygon_info_to_geometry(polygon_info)
        if geometry is None:
            continue

        adjusted_geometry = geometry.difference(annotated_union)
        if not adjusted_geometry.is_valid:
            adjusted_geometry = adjusted_geometry.buffer(0)

        adjusted_polygon_infos.extend(
            geometry_to_polygon_infos(adjusted_geometry, polygon_info)
        )

    return adjusted_polygon_infos


def get_generate_polygons_handler() -> IGeneratePolygonsHandler:
    """Return the polygon-generation handler selected by configuration."""
    sam_backend = os.getenv("SAM_BACKEND", "local").lower()
    if sam_backend == "lambda":
        return LambdaGeneratePolygonsHandler()
    if sam_backend == "runpod":
        return RunPodGeneratePolygonsHandler()
    if sam_backend == "local":
        return LocalGeneratePolygonsHandler()
    raise ValueError(f"Unsupported SAM backend: {sam_backend}")

# def create_prompts(prompts):
#     positive_points = [[100, 150], [200, 250]]
#     negative_points = [[300, 350], [400, 450]]
#     bbox = [50, 50, 400, 400]
#     return Prompts(positive_points=positive_points, negative_points=negative_points, bbox=bbox)


@route("projects/data/generate-polygons")
class GeneratePolygonsController(Controller):
    def process_post_request(self, request_object):
        print(request_object)
        image_id = request_object.image_id
        # prompts = request_object.prompts
        image_info = dbh.get_image_info(image_id)
        # image_info = dbh
        image_url = image_info["imageUrls"]["jpg"]
        image_width = image_info["imageWidth"]
        image_height = image_info["imageHeight"]
        # Scale the image to a width of 1024 pixels
        new_image_size = utils.scale_image_size_to_max_dim_if_larger(
            (image_width, image_height), 1024
        )
        sam_prompts = convert_prompts_to_sam_payload(request_object.prompts)
        sw = stopwatch.Stopwatch()
        sw.start()
        # Generate polygons using the SAM model
        model_config = ModelConfig(
            points_per_side=30,
            pred_iou_thresh=0.5,
            stability_score_thresh=0.5,
            crop_n_layers=1,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=1000,
        )
        input_payload = {
            "input": {
                "image_info": {
                    "image_url": image_url,
                    "image_size": (image_width, image_height),
                    "new_image_size": new_image_size,
                },
                "model_config": model_config,
                "prompts": sam_prompts,
            }
        }
        generation_handler = get_generate_polygons_handler()
        polygons = generation_handler.generate(input_payload)
        pod_polygon_infos = [
            convert_worker_polygon_to_polygon_info(polygon)
            for polygon in polygons
        ]
        sw.stop()
        print(sw.total_seconds)
        annotated_polygon_infos = dbh.get_annotated_polygons(image_id)
        pod_polygon_infos = remove_annotated_polygon_overlaps(
            pod_polygon_infos,
            annotated_polygon_infos,
        )

        dbh.save_polygon_infos(image_id, pod_polygon_infos)
        db_polygon_infos = dbh.get_polygons(image_id)
        return ok(db_polygon_infos)
