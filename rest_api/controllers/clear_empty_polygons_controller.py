from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh


@route("projects/data/clear-empty-polygons")
class ClearEmptyPolygonsController(Controller):
    def process_post_request(self, request_object):
        image_id = request_object.image_id
        deleted_count = dbh.delete_empty_polygon_infos(image_id)
        db_polygon_infos = dbh.get_polygons(image_id)
        return ok(db_polygon_infos)
