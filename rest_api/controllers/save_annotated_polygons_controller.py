
from ..controller import *
from ..decorators.route import route


@route('save_annotated_polygons')
class SaveAnnotatedPolygonsController(Controller):
    def process_post_request(self, request_object):
        pass
