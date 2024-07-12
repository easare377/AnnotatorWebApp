from ..controller import *
from ..decorators.route import route
from ..dbhelper import *


@route('projects/data/annotate')
class GetPolygonsController(Controller):
    def process_post_request(self, request_object):
        polygon_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        image_id = models.ForeignKey(ImageInfo, on_delete=models.CASCADE, null=False)
        class_id = models.ForeignKey(ObjectClass, on_delete=models.CASCADE)
        points = models.JSONField(null=False)
        stability_score = models.FloatField(null=False)
        predicted_iou = models.FloatField(null=False)
        date_created = models.DateTimeField(default=timezone.now, null=False)
        date_modified = models.DateTimeField(auto_now=True)

        return ok([{'polygonId': '1234',
                    'classId': '3456',
                    'points': [{'x': 6, 'y': 6}, {'x': 8, 'y': 4}, {'x': 3, 'y': 7}],
                    'stabilityScore': 1.0,
                    'predictedIoU': 1.0,
                    'dateCreated': timezone.now(),
                    'dateModified': timezone.now()}])
        pass
