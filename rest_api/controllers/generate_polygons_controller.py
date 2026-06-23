from rest_api.objects.model_config import ModelConfig
import os

from ..controller import *
from ..decorators.route import route

# from rest_api.utils import sam as sam
from rest_api import dbhelper as dbh
import requests
import runpod
from ..utils.runpod_polygon_info import RunPodPolygonInfo
from rest_api import stopwatch


def convert_to_jsonable(value):
    if isinstance(value, dict):
        return {key: convert_to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [convert_to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return convert_to_jsonable(vars(value))
    return value

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


def generate_polygons_from_runpod(input_payload):
    runpod.api_key = "5AKXD6UDVL773K7OGNG7OSEOUPZWX3BLM57XNM33"
    endpoint = runpod.Endpoint("adoqht5dtckgr7")
    polygons = endpoint.run_sync(input_payload, timeout=120)
    return polygons


def generate_polygons_from_sam_local(input_payload):
    sam_local_url = os.getenv("SAM_WORKER_LOCAL_URL", "http://localhost:8000/run")
    if not sam_local_url.endswith("/run"):
        sam_local_url = f"{sam_local_url.rstrip('/')}/run"

    response = requests.post(
        sam_local_url,
        json=convert_to_jsonable(input_payload),
        timeout=120,
    )
    response.raise_for_status()

    worker_output = response.json()
    return worker_output.get("output", worker_output)


def generate_polygons(image_url, image_size, new_image_size, prompts):
    image_info = {
        "image_url": image_url,
        "image_size": image_size,
        "new_image_size": new_image_size,
    }
    model_config = ModelConfig(points_per_side=30, 
                               pred_iou_thresh=0.5, 
                               stability_score_thresh=0.5,
                                crop_n_layers=1, 
                                crop_n_points_downscale_factor=2, 
                                min_mask_region_area=1000)

    # polygons = worker_output["output"]
    input_payload = {
        "input": {
            "image_info": image_info,
            "model_config": model_config,
            "prompts": prompts
        }
    }
    # polygons = generate_polygons_from_runpod(input_payload)
    polygons = generate_polygons_from_sam_local(input_payload)
    polygons = [
        [{"x": point[0], "y": point[1]} for point in points] for points in polygons
    ]
    polygon_infos = []
    for polygon in polygons:
        polygon_info = RunPodPolygonInfo(1.0, 1.0, polygon)
        polygon_infos.append(polygon_info)
    return polygon_infos

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
        prompts = request_object.prompts
        image_info = dbh.get_image_info(image_id)
        # image_info = dbh
        image_url = image_info["imageUrls"]["jpg"]
        image_width = image_info["imageWidth"]
        image_height = image_info["imageHeight"]
        new_image_size = utils.scale_image_size_to_width(
            (image_width, image_height), 1000
        )
        sam_prompts = convert_prompts_to_sam_payload(request_object.prompts)
        sw = stopwatch.Stopwatch()
        sw.start()
        pod_polygon_infos = generate_polygons(
            image_url,
            (image_width, image_height),
            new_image_size,
            sam_prompts,
        )
        sw.stop()
        print(sw.total_seconds)
        db_polygon_infos = dbh.save_polygon_infos(image_id, pod_polygon_infos)
        return ok(db_polygon_infos)
