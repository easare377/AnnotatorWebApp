from ..controller import *
from ..decorators.route import route
# from rest_api.utils import sam as sam
from rest_api import dbhelper as dbh
import runpod
from ..utils.runpod_polygon_info import RunPodPolygonInfo


def generate_polygons(image_url):
    runpod.api_key = "5AKXD6UDVL773K7OGNG7OSEOUPZWX3BLM57XNM33"
    input_payload = {"input":
        {
            "image_url": image_url,
            "points_per_side": 20,
            "pred_iou_thresh": 0.7,
            "stability_score_thresh": 0.7
        }
    }

    # endpoint = runpod.Endpoint("q3st7apndadh4o")
    endpoint = runpod.Endpoint("s9tso198s4wlcm")
    polygons = endpoint.run_sync(input_payload, timeout=120)
    # polygons = worker_output["output"]
    polygons = [
        [{'x': point[0], 'y': point[1]} for point in points]
        for points in polygons
    ]
    polygon_infos = []
    for polygon in polygons:
        polygon_info = RunPodPolygonInfo(1.0, 1.0, polygon)
        # polygon_info = {
        #     'stabilityScore': 1.0,
        #     'predictedIoU': 1.0,
        #     'points': polygon
        # }
        polygon_infos.append(polygon_info)
    return polygon_infos


@route('projects/data/generate-polygons')
class GeneratePolygonsController(Controller):
    def process_post_request(self, request_object):
        image_id = request_object.image_id
        image_info = dbh.get_image_info(image_id)
        # image_info = dbh
        image_url = image_info["imageUrl"]
        pod_polygon_infos = generate_polygons(image_url)
        db_polygon_infos = dbh.save_polygon_infos(image_id, pod_polygon_infos)
        return ok(db_polygon_infos)
