class RunPodPolygonInfo:
    def __init__(self, stability_score, predicted_iou, points):
        self.stability_score = stability_score
        self.predicted_iou = predicted_iou
        self.points = points
