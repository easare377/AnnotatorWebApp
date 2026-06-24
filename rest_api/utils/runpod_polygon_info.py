class RunPodPolygonInfo:
    def __init__(self, stability_score, predicted_iou, points, inner_polygons):
        self.stability_score = stability_score
        self.predicted_iou = predicted_iou
        self.points = points
        self.inner_polygons = inner_polygons
