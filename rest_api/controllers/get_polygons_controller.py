from ..controller import *
from ..decorators.route import route
from ..dbhelper import *
from rest_api import dbhelper as dbh


@route('projects/data/polygons')
class GetPolygonsController(Controller):
    def process_post_request(self, request_object):
        image_id = request_object.image_id
        db_polygon_infos = dbh.get_polygons(image_id)
        # if len(db_polygon_infos) == 0:
        #     pod_polygon_infos = generate_polygons(image_url)
        #     db_polygon_infos = dbh.save_polygon_infos(image_id, pod_polygon_infos)
        return ok(db_polygon_infos)
