from ..controller import *
from ..decorators.route import route
from rest_api.utils import sam as sam
from rest_api import dbhelper as dbh

def generate_polygons(image_url):
    runpod.api_key = "08BKGQXTXCQW8E51IDIQOO74EY3YRBQEYL3FTURU"
    input_payload = {"input":
        {
            "image_url": image_url
        }
    }
    endpoint = runpod.Endpoint("a88wccan78n79h")
    worker_output = endpoint.run_sync(input_payload, timeout=120)
    polygons = worker_output["output"]
    polygons = [
        [{'x': point[0], 'y': point[1]} for point in points]
        for points in polygons
    ]
    polygon_infos = []
    for polygon in polygons:
        polygon_info = {
            'stabilityScore': 1.0,
            'predictedIoU': 1.0,
            'points': polygon
        }
        polygon_infos.append(polygon_info)
    return polygon_infos


@route('generate-polygons')
class GeneratePolygonsController(Controller):
    def process_post_request(self, request_object):
        image_id = request_object.image_id
        # image_info = dbh
        image_url = request_object.image_url
        pod_polygon_infos = generate_polygons(image_url)
        db_polygon_infos = dbh.save_polygon_infos(image_id, pod_polygon_infos)
        return ok(db_polygon_infos)
